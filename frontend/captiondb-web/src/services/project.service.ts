import { apiClient } from "@/lib/api-client";
import { ProjectDTO, ProjectListResponse } from "@/types/api";

const PROJECT_BASE = "/v1/projects";

export const projectService = {
  async listProjects(limit = 100, offset = 0): Promise<ProjectListResponse> {
    return apiClient.get<ProjectListResponse>(`${PROJECT_BASE}/`, {
      params: { limit, offset },
    });
  },

  async getProject(projectId: string): Promise<ProjectDTO> {
    return apiClient.get<ProjectDTO>(`${PROJECT_BASE}/${projectId}`);
  },

  async deleteProject(projectId: string): Promise<void> {
    return apiClient.delete<void>(`${PROJECT_BASE}/${projectId}`);
  },

  async duplicateProject(projectId: string): Promise<ProjectDTO> {
    return apiClient.post<ProjectDTO>(`${PROJECT_BASE}/${projectId}/duplicate`);
  },

  async processProject(projectId: string): Promise<{ status: string; message: string }> {
    return apiClient.post<{ status: string; message: string }>(`${PROJECT_BASE}/${projectId}/process`);
  }
};
