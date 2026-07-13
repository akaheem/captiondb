"use client";

import { useProjects } from "@/hooks/use-projects";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DashboardSkeleton } from "@/components/ui/skeletons";
import { ProcessingMonitor } from "@/components/dashboard/processing-monitor";

export default function DashboardPage() {
  const { data, isLoading, error } = useProjects(5, 0);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center border rounded-lg border-destructive/20 bg-destructive/10 text-destructive">
        <h3 className="font-semibold text-lg">Error loading dashboard</h3>
        <p className="text-sm">Please try again later.</p>
      </div>
    );
  }

  const projects = data?.data || [];
  const totalProjects = data?.total || 0;
  
  const completedProjects = projects.filter(p => p.status === "COMPLETED").length;
  const processingProjects = projects.filter(p => p.status === "PROCESSING").length;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back. Here's an overview of your projects.
          </p>
        </div>
        <Link href="/dashboard/projects/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Projects</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalProjects}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedProjects}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{processingProjects}</div>
          </CardContent>
        </Card>
      </div>

      <ProcessingMonitor
        description="Live status of your current AI processing jobs."
        limit={10}
      />

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Recent Projects</h2>
          <Link href="/dashboard/projects">
            <Button variant="link">View All</Button>
          </Link>
        </div>
        
        {projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center border rounded-lg border-dashed">
            <h3 className="font-semibold text-lg">No projects yet</h3>
            <p className="text-sm text-muted-foreground mt-1 mb-4">
              Get started by uploading your first video.
            </p>
            <Link href="/dashboard/projects/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Upload Video
              </Button>
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Card key={project.id}>
                <CardHeader>
                  <CardTitle className="truncate">{project.project_name}</CardTitle>
                  <CardDescription>
                    Status: <span className="font-semibold">{project.status}</span>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Link href={`/dashboard/projects/${project.id}`}>
                    <Button variant="outline" className="w-full">
                      View Details
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
