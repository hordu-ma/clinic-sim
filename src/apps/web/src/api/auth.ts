import request from "./request";

export const login = (data: any) => {
  return request({
    url: "/auth/login",
    method: "post",
    data,
  });
};

export const getUserInfo = () => {
  return request({
    url: "/auth/me",
    method: "get",
  });
};
