// src/hooks/useUser.js

import {
    useEffect,
    useState,
  } from "react";
  
  import {
    getMe,
  } from "../api/userApi";
  
  export default function useUser() {
  
    const [user,
      setUser] =
      useState(null);
  
    async function load() {
  
      const response =
        await getMe();
  
      setUser(
        response.data
      );
  
    }
  
    useEffect(() => {
      load();
    }, []);
  
    return {
      user,
      reload: load,
    };
  }