"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Plus, Trash, Eye, Copy } from "lucide-react";
import { toast } from "sonner";

import {
  useProjects,
  useDeleteProject,
  useDuplicateProject,
} from "@/hooks/use-projects";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DashboardSkeleton } from "@/components/ui/skeletons";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { ProjectStatusBadge } from "@/components/projects/project-status-badge";
import {
  ProjectsToolbar,
  type SortKey,
  type StatusFilter,
} from "@/components/projects/projects-toolbar";
import { formatDateTime } from "@/lib/format";
import type { ProjectDTO } from "@/types/api";

const PAGE_SIZE = 10;

export default function ProjectsPage() {
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilter>("ALL");
  const [sort, setSort] = useState<SortKey>("created_desc");
  const [pendingDelete, setPendingDelete] = useState<ProjectDTO | null>(null);

  const { data, isLoading, error } = useProjects(PAGE_SIZE, page * PAGE_SIZE);
  const deleteProject = useDeleteProject();
  const duplicateProject = useDuplicateProject();

  const total = data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const visibleProjects = useMemo(() => {
    const projects = data?.data ?? [];
    const term = search.trim().toLowerCase();

    const filtered = projects.filter((project) => {
      const matchesSearch =
        !term || project.project_name.toLowerCase().includes(term);
      const matchesStatus = status === "ALL" || project.status === status;
      return matchesSearch && matchesStatus;
    });

    const sorted = [...filtered].sort((a, b) => {
      switch (sort) {
        case "name_asc":
          return a.project_name.localeCompare(b.project_name);
        case "name_desc":
          return b.project_name.localeCompare(a.project_name);
        case "created_asc":
          return (
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          );
        case "created_desc":
        default:
          return (
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          );
      }
    });

    return sorted;
  }, [data?.data, search, status, sort]);

  const handleDuplicate = async (project: ProjectDTO) => {
    try {
      await duplicateProject.mutateAsync(project.id);
      toast.success(`Duplicated "${project.project_name}"`);
    } catch {
      toast.error("Failed to duplicate project");
    }
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    const target = pendingDelete;
    try {
      await deleteProject.mutateAsync(target.id);
      toast.success(`Deleted "${target.project_name}"`);
      setPendingDelete(null);
    } catch {
      toast.error("Failed to delete project");
    }
  };

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-destructive/20 bg-destructive/10 p-8 text-center text-destructive">
        <h3 className="text-lg font-semibold">Error loading projects</h3>
        <p className="text-sm">Please try again later.</p>
      </div>
    );
  }

  const hasProjectsOnPage = (data?.data ?? []).length > 0;
  const isFiltering = search.trim() !== "" || status !== "ALL";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground">
            Manage your uploaded videos and caption projects.
          </p>
        </div>
        <Link href="/dashboard/projects/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        </Link>
      </div>

      <ProjectsToolbar
        search={search}
        onSearchChange={setSearch}
        status={status}
        onStatusChange={setStatus}
        sort={sort}
        onSortChange={setSort}
      />

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {visibleProjects.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={4}
                  className="py-8 text-center text-muted-foreground"
                >
                  {isFiltering
                    ? "No projects match your filters."
                    : "No projects found."}
                </TableCell>
              </TableRow>
            ) : (
              visibleProjects.map((project) => (
                <TableRow key={project.id}>
                  <TableCell className="font-medium">
                    <Link
                      href={`/dashboard/projects/${project.id}`}
                      className="hover:underline"
                    >
                      {project.project_name}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <ProjectStatusBadge status={project.status} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDateTime(project.created_at)}
                  </TableCell>
                  <TableCell className="space-x-2 text-right">
                    <Link href={`/dashboard/projects/${project.id}`}>
                      <Button variant="outline" size="sm">
                        <Eye className="mr-1 h-4 w-4" />
                        View
                      </Button>
                    </Link>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDuplicate(project)}
                      disabled={duplicateProject.isPending}
                    >
                      <Copy className="mr-1 h-4 w-4" />
                      Duplicate
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setPendingDelete(project)}
                    >
                      <Trash className="mr-1 h-4 w-4" />
                      Delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {total > 0
            ? `Showing ${visibleProjects.length} of ${total} project${
                total === 1 ? "" : "s"
              }`
            : "No projects yet"}
        </span>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
          >
            Previous
          </Button>
          <span>
            Page {page + 1} of {pageCount}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={page + 1 >= pageCount || !hasProjectsOnPage}
          >
            Next
          </Button>
        </div>
      </div>

      <ConfirmDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => {
          if (!open) setPendingDelete(null);
        }}
        title="Delete project?"
        description={
          pendingDelete ? (
            <>
              This permanently deletes{" "}
              <span className="font-medium text-foreground">
                {pendingDelete.project_name}
              </span>{" "}
              and its results. This action cannot be undone.
            </>
          ) : null
        }
        confirmLabel="Delete"
        loading={deleteProject.isPending}
        onConfirm={confirmDelete}
      />
    </div>
  );
}
