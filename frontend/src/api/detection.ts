import request from "@/utils/request";
import type { SingleDetectionResponse } from "./types";

export function detectSingleImage(data: any): Promise<SingleDetectionResponse> {
  return request({
    url: "/detection/single",
    method: "post",
    data,
  });
}

export function detectBatchImages(
  data: any,
): Promise<SingleDetectionResponse[]> {
  return request({
    url: "/detection/batch",
    method: "post",
    data,
  });
}
