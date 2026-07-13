import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadService } from "@/services/upload.service";
import { projectKeys } from "./use-projects";

export function useUploadVideo() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ projectName, file, onProgress }: { projectName: string; file: File; onProgress?: (progressEvent: any) => void }) => 
      uploadService.uploadVideo(projectName, file, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() });
    },
  });
}
