"use client";

import { useState } from "react";
import { useProject, useProcessProject, useDeleteProject, useDuplicateProject } from "@/hooks/use-projects";
import { Button } from "@/components/ui/button";
import { Play, Trash, Copy, ArrowLeft, Sparkles } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DashboardSkeleton } from "@/components/ui/skeletons";
import { toast } from "sonner";
import { Separator } from "@/components/ui/separator";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { ProjectStatusBadge } from "@/components/projects/project-status-badge";
import { formatBytes } from "@/lib/format";

export default function ProjectDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const { data: project, isLoading, error } = useProject(projectId);
  const processProject = useProcessProject();
  const deleteProject = useDeleteProject();
  const duplicateProject = useDuplicateProject();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleProcess = async () => {
    try {
      await processProject.mutateAsync(projectId);
      toast.success("Processing started successfully");
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string };
      toast.error("Failed to start processing", {
        description: err.response?.data?.detail || err.message,
      });
    }
  };

  const handleDelete = async () => {
    try {
      await deleteProject.mutateAsync(projectId);
      toast.success("Project deleted successfully");
      router.push("/dashboard/projects");
    } catch {
      toast.error("Failed to delete project");
    }
  };

  const handleDuplicate = async () => {
    try {
      const newProject = await duplicateProject.mutateAsync(projectId);
      toast.success("Project duplicated successfully");
      router.push(`/dashboard/projects/${newProject.id}`);
    } catch {
      toast.error("Failed to duplicate project");
    }
  };

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error || !project) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center border rounded-lg border-destructive/20 bg-destructive/10 text-destructive">
        <h3 className="font-semibold text-lg">Error loading project</h3>
        <p className="text-sm">Please try again later or verify the project exists.</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push("/dashboard/projects")}>
          Back to Projects
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Link href="/dashboard/projects">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{project.project_name}</h1>
          <p className="text-muted-foreground flex items-center gap-2">
            <span>Status:</span>
            <ProjectStatusBadge status={project.status} />
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Video Metadata</CardTitle>
            <CardDescription>Intrinsic details extracted during upload.</CardDescription>
          </CardHeader>
          <CardContent>
            {project.metadata ? (
              <dl className="grid grid-cols-2 gap-x-4 gap-y-4 text-sm">
                <div>
                  <dt className="text-muted-foreground font-medium">Duration</dt>
                  <dd>{project.metadata.duration_seconds.toFixed(2)} seconds</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground font-medium">Size</dt>
                  <dd>{formatBytes(project.metadata.size_bytes)}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground font-medium">Resolution</dt>
                  <dd>{project.metadata.resolution} ({project.metadata.dimensions.width}x{project.metadata.dimensions.height})</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground font-medium">Framerate</dt>
                  <dd>{project.metadata.fps} FPS</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground font-medium">Codec</dt>
                  <dd>{project.metadata.codec}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground font-medium">Format</dt>
                  <dd>{project.metadata.format}</dd>
                </div>
              </dl>
            ) : (
              <div className="text-muted-foreground italic">No metadata available.</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              className="w-full"
              onClick={handleProcess}
              disabled={project.status !== "PENDING" || processProject.isPending}
            >
              <Play className="mr-2 h-4 w-4" />
              Start Processing
            </Button>

            {project.status === "COMPLETED" && (
              <Link href={`/dashboard/projects/${projectId}/results`} className="block">
                <Button variant="secondary" className="w-full">
                  <Sparkles className="mr-2 h-4 w-4" />
                  View AI Results
                </Button>
              </Link>
            )}

            <Separator />
            
            <Button 
              variant="outline" 
              className="w-full"
              onClick={handleDuplicate}
              disabled={duplicateProject.isPending}
            >
              <Copy className="mr-2 h-4 w-4" />
              Duplicate Project
            </Button>
            
            <Button
              variant="destructive"
              className="w-full"
              onClick={() => setConfirmDelete(true)}
              disabled={deleteProject.isPending}
            >
              <Trash className="mr-2 h-4 w-4" />
              Delete Project
            </Button>
          </CardContent>
        </Card>
      </div>

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Delete project?"
        description={
          <>
            This permanently deletes{" "}
            <span className="font-medium text-foreground">
              {project.project_name}
            </span>{" "}
            and its results. This action cannot be undone.
          </>
        }
        confirmLabel="Delete"
        loading={deleteProject.isPending}
        onConfirm={handleDelete}
      />
    </div>
  );
}
