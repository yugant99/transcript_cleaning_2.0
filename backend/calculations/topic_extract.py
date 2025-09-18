#!/usr/bin/env python3
import json
import os
import pickle
from collections import defaultdict, Counter

import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer


def load_processed(path: str):
    with open(path, 'rb') as f:
        data = pickle.load(f)
    embeddings = np.array(data['embeddings'])
    chunk_metadata = data['chunk_metadata']
    return embeddings, chunk_metadata


def extract_texts_and_meta(chunk_metadata):
    texts = []
    metas = []
    for cm in chunk_metadata:
        text = cm.get('chunk_text', '') or ''
        file_meta = cm.get('file_metadata', {}) or {}
        metas.append({
            'chunk_index': cm.get('chunk_index', 0),
            'text': text,
            'filename': file_meta.get('filename') or os.path.basename(file_meta.get('file_path', '') or 'unknown'),
            'patient_id': file_meta.get('patient_id', 'Unknown'),
            'session_type': file_meta.get('session_type', 'Unknown'),
            'week_label': file_meta.get('week_label', 'Unknown'),
            'condition': file_meta.get('condition', 'Unknown'),
        })
        texts.append(text)
    return texts, metas


def cluster_embeddings(embeddings: np.ndarray, n_clusters: int = 15, random_state: int = 42):
    kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=random_state, batch_size=2048, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    return kmeans, labels


def label_topics(texts, labels, n_top_terms: int = 5):
    vectorizer = TfidfVectorizer(max_features=8000, stop_words='english', ngram_range=(1, 2), min_df=2, max_df=0.8)
    tfidf = vectorizer.fit_transform(texts)
    feature_names = np.array(vectorizer.get_feature_names_out())

    topics = []
    for t in sorted(set(labels)):
        idx = np.where(labels == t)[0]
        if len(idx) == 0:
            topics.append({'id': int(t), 'label': f'Topic {t}', 'top_terms': [], 'size': 0})
            continue
        # mean tf-idf within cluster
        cluster_tfidf = tfidf[idx].mean(axis=0).A1
        top_idx = cluster_tfidf.argsort()[-n_top_terms:][::-1]
        top_terms = feature_names[top_idx].tolist()
        label = ', '.join(top_terms[:3]) if top_terms else f'Topic {t}'
        topics.append({'id': int(t), 'label': label, 'top_terms': top_terms, 'size': int(len(idx))})
    return topics


def aggregate_by_file(labels, metas, topics):
    topic_id_to_label = {t['id']: t['label'] for t in topics}
    # per file counts and switches
    files = defaultdict(lambda: {
        'metadata': None,
        'topic_counts': Counter(),
        'switch_counts': Counter(),
        'chunks': []
    })

    for i, m in enumerate(metas):
        fname = m['filename']
        files[fname]['chunks'].append({'idx': m['chunk_index'], 'topic': int(labels[i]), 'text': m['text']})
        files[fname]['topic_counts'][int(labels[i])] += 1
        if files[fname]['metadata'] is None:
            files[fname]['metadata'] = {
                'patient_id': m['patient_id'],
                'session_type': m['session_type'],
                'week_label': m['week_label'],
                'condition': m['condition'],
                'filename': fname,
            }

    # compute switches and top topics, shares
    out_by_file = {}
    for fname, data in files.items():
        chunks_sorted = sorted(data['chunks'], key=lambda x: x['idx'])
        for i in range(1, len(chunks_sorted)):
            a = chunks_sorted[i-1]['topic']
            b = chunks_sorted[i]['topic']
            if a != b:
                key = f"{a}->{b}"
                data['switch_counts'][key] += 1

        total_chunks = sum(data['topic_counts'].values()) or 1
        topic_share = {str(k): round(v/total_chunks*100, 2) for k, v in data['topic_counts'].items()}
        top_topics = [int(tid) for tid,_ in data['topic_counts'].most_common(3)]
        out_by_file[fname] = {
            'metadata': data['metadata'],
            'topic_counts': {str(k): int(v) for k, v in data['topic_counts'].items()},
            'topic_share': topic_share,
            'top_topics': top_topics,
            'switch_counts': dict(data['switch_counts']),
        }
    return out_by_file, topic_id_to_label


def build_examples(labels, metas, topics, max_per_topic=50, max_switch_examples=50):
    by_topic = defaultdict(list)
    # collect per-topic examples
    for i, m in enumerate(metas):
        t = int(labels[i])
        if len(by_topic[t]) < max_per_topic:
            by_topic[t].append({
                'text': (m['text'] or '')[:300],
                'filename': m['filename'],
                'patient_id': m['patient_id'],
                'week_label': m['week_label'],
                'session_type': m['session_type'],
                'condition': m['condition'],
            })

    # switches examples: take boundary chunks when topic changes
    switches = defaultdict(list)
    # group by file
    by_file_chunks = defaultdict(list)
    for i, m in enumerate(metas):
        by_file_chunks[m['filename']].append({'idx': m['chunk_index'], 'topic': int(labels[i]), 'meta': m})
    for fname, arr in by_file_chunks.items():
        arr.sort(key=lambda x: x['idx'])
        for i in range(1, len(arr)):
            a = arr[i-1]
            b = arr[i]
            if a['topic'] != b['topic']:
                key = f"{a['topic']}->{b['topic']}"
                if len(switches[key]) >= max_switch_examples:
                    continue
                m = b['meta']
                switches[key].append({
                    'snippet': (m['text'] or '')[:300],
                    'filename': m['filename'],
                    'patient_id': m['patient_id'],
                    'week_label': m['week_label'],
                    'session_type': m['session_type'],
                    'condition': m['condition'],
                })
    return {str(int(k)): v for k, v in by_topic.items()}, switches


def main():
    processed_path = os.path.join(os.path.dirname(__file__), '../../processed_data/master_transcripts.pkl')
    embeddings, chunk_metadata = load_processed(processed_path)
    texts, metas = extract_texts_and_meta(chunk_metadata)

    # Filter out empty texts to avoid degenerate TF-IDF rows
    mask = np.array([bool((t or '').strip()) for t in texts])
    if mask.sum() == 0:
        raise RuntimeError('No valid texts found for topic extraction')
    texts = [texts[i] for i in range(len(texts)) if mask[i]]
    metas = [metas[i] for i in range(len(metas)) if mask[i]]
    embeddings = embeddings[mask]

    kmeans, labels = cluster_embeddings(embeddings, n_clusters=15)
    topics = label_topics(texts, labels)
    by_file, topic_id_to_label = aggregate_by_file(labels, metas, topics)
    by_topic_examples, switch_examples = build_examples(labels, metas, topics)

    out = {
        'topics': topics,
        'by_file': by_file,
        'examples': {
            'by_topic': by_topic_examples,
            'switches': switch_examples,
        }
    }

    out_dir = os.path.join(os.path.dirname(__file__), '../outputfile')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'topic_model.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"✅ Wrote {out_path} with {len(topics)} topics and {len(by_file)} files")


if __name__ == '__main__':
    main()


