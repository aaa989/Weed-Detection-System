import request from "../utils/request";

export const videoUploadAndDetect = (formData) => {
  return request({
    url: "/detection/video/upload",
    method: "post",
    data: formData,
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60000,
  });
};

export const getVideoStatus = (taskId) => {
  return request({
    url: `/detection/video/status/${taskId}`,
    method: "get",
  });
};