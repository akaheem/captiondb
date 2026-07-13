"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useUploadVideo } from "@/hooks/use-upload";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const uploadSchema = z.object({
  projectName: z.string().min(3, "Project name must be at least 3 characters"),
  file: z.any()
    .refine((fileList) => fileList instanceof FileList && fileList.length > 0, "Video file is required")
    .refine((fileList) => fileList[0]?.size <= 100 * 1024 * 1024, "Max file size is 100MB")
    .refine(
      (fileList) => ["video/mp4", "video/webm", "video/ogg"].includes(fileList[0]?.type),
      "Only MP4, WEBM, and OGG formats are supported"
    ),
});

export default function NewProjectPage() {
  const router = useRouter();
  const { mutateAsync: uploadVideo } = useUploadVideo();
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const form = useForm<z.infer<typeof uploadSchema>>({
    resolver: zodResolver(uploadSchema),
    defaultValues: {
      projectName: "",
    },
  });

  const onSubmit = async (values: z.infer<typeof uploadSchema>) => {
    try {
      setIsUploading(true);
      setProgress(0);
      const file = values.file[0];
      
      const response = await uploadVideo({
        projectName: values.projectName,
        file,
        onProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setProgress(percentCompleted);
          }
        },
      });

      if (response.success) {
        toast.success("Video uploaded successfully!");
        router.push(`/dashboard/projects/${response.video_id}`);
      } else {
        toast.error("Upload failed", {
          description: response.errors?.join(", ") || "Unknown error occurred"
        });
      }
    } catch (error: any) {
      toast.error("Upload failed", {
        description: error.message || "An error occurred while uploading the video."
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">New Project</h1>
        <p className="text-muted-foreground">
          Upload a video to start a new captioning project.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Video Details</CardTitle>
          <CardDescription>
            Provide a name and select your video file.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="projectName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Project Name</FormLabel>
                    <FormControl>
                      <Input placeholder="E.g., Marketing Video 2026" {...field} disabled={isUploading} />
                    </FormControl>
                    <FormDescription>
                      This will be used to identify your project.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="file"
                render={({ field: { value, onChange, ...field } }) => (
                  <FormItem>
                    <FormLabel>Video File</FormLabel>
                    <FormControl>
                      <Input 
                        type="file" 
                        accept="video/mp4,video/webm,video/ogg"
                        disabled={isUploading}
                        onChange={(e) => onChange(e.target.files)}
                        {...field} 
                      />
                    </FormControl>
                    <FormDescription>
                      Max size: 100MB. Supported formats: MP4, WEBM, OGG.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {isUploading && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Uploading...</span>
                    <span>{progress}%</span>
                  </div>
                  <Progress value={progress} />
                </div>
              )}

              <div className="flex justify-end space-x-4">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => router.back()}
                  disabled={isUploading}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isUploading}>
                  {isUploading ? "Uploading..." : "Upload Video"}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
