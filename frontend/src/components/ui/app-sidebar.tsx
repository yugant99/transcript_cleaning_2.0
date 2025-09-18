"use client"

import {
  BarChart3,
  FileText,
  Home,
  Settings,
  Users,
  Brain,
  TrendingUp,
  Database,
  MessageSquare,
  Heart,
} from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

// Menu items
const items = [
  {
    title: "Glossary",
    url: "/dashboard/glossary",
    icon: FileText,
  },
  {
    title: "Summary",
    url: "/dashboard",
    icon: Home,
  },
  {
    title: "Questions & Answers",
    url: "/dashboard/questions",
    icon: MessageSquare,
  },
  {
    title: "Sentiment Analysis",
    url: "/dashboard/sentiment",
    icon: Heart,
  },
  {
    title: "Lexical Diversity",
    url: "/dashboard/lexical",
    icon: BarChart3,
  },
  {
    title: "Non Verbal",
    url: "/dashboard/nonverbal",
    icon: Users,
  },
  {
    title: "Disfluency",
    url: "/dashboard/disfluency",
    icon: MessageSquare,
  },
  {
    title: "Word Repeats",
    url: "/dashboard/word-repeats",
    icon: MessageSquare,
  },
  {
    title: "Topic Explorer",
    url: "/dashboard/topics",
    icon: Brain,
  },
  {
    title: "Total View",
    url: "/dashboard/total-view",
    icon: Database,
  },
  {
    title: "Semantic Insights",
    url: "/dashboard/semantic",
    icon: Brain,
  },
  {
    title: "Turn Taking",
    url: "/dashboard/turn-taking",
    icon: Users,
  },
  {
    title: "Trends & Patterns",
    url: "/dashboard/trends",
    icon: TrendingUp,
  },
  {
    title: "Data Export",
    url: "/dashboard/export",
    icon: Database,
  },
]

const adminItems = [
  {
    title: "Reports",
    url: "/dashboard/reports",
    icon: FileText,
  },
  {
    title: "Analytics",
    url: "/dashboard/analytics",
    icon: BarChart3,
  },
  {
    title: "Settings",
    url: "/dashboard/settings",
    icon: Settings,
  },
]

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Dashboard</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <a href={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel>Administration</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {adminItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <a href={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <div className="p-4 text-sm text-muted-foreground">
          <p className="font-medium">NLP Analysis v2.0</p>
          <p>Powered by AI</p>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
