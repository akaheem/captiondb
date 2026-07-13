import { apiClient } from "@/lib/api-client";
import { UploadResponse } from "@/types/api";

const UPLOAD_BASE = "/v1/upload";

export const uploadService = {
  async uploadVideo(projectName: string, file: File, onProgress?: (progressEvent: any) => void): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("project_name", projectName);
    formData.append("file", file);

    return apiClient.post<UploadResponse>(`${UPLOAD_BASE}/`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: onProgress,
    });
  },
};
