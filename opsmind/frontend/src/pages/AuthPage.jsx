// src/pages/AuthPage.jsx

import { useState } from "react";
import { login, register } from "../api/authApi";

import {
  login,
  register,
  me,
} from "../api/authApi";

import { useAuth } from "../context/AuthContext";

export default function AuthPage() {
  const { setUser } =
    useAuth();

  const [tab, setTab] =
    useState("login");

  const [loading, setLoading] =
    useState(false);

  const [form, setForm] =
    useState({
      email: "",
      password: "",
      username: "",
      full_name: "",
      phone: "",
    });


    
    async function submit(e) {
    
      e.preventDefault();
    
      setLoading(true);
      setError("");
    
      try {
    
        let response;
    
        if (tab === "login") {
    
          response = await login({
            identifier: form.email,
            password: form.password,
          });
    
        } else {
    
          response = await register({
            email: form.email,
            phone: form.phone || null,
            username: form.username,
            full_name: form.full_name,
            password: form.password,
            auth_provider: "email",
          });
    
        }
    
        localStorage.setItem(
          "access_token",
          response.data.access_token
        );
    
        localStorage.setItem(
          "refresh_token",
          response.data.refresh_token
        );
    
        onLogin({
          email: form.email,
          username:
            form.username ||
            form.email.split("@")[0],
        });
    
      } catch (error) {
    
        console.error(error);
    
        setError(
          error.response?.data?.detail ||
          "Authentication failed"
        );
    
      } finally {
    
        setLoading(false);
    
      }
    }

  return (
    <div>
      <h1>OpsMind</h1>

      <button
        onClick={() =>
          setTab("login")
        }
      >
        Login
      </button>

      <button
        onClick={() =>
          setTab(
            "register"
          )
        }
      >
        Register
      </button>

      <form
        onSubmit={submit}
      >
        {tab ===
          "register" && (
          <>
            <input
              placeholder="Full name"
              value={
                form.full_name
              }
              onChange={(e) =>
                setForm({
                  ...form,
                  full_name:
                    e.target
                      .value,
                })
              }
            />

            <input
              placeholder="Username"
              value={
                form.username
              }
              onChange={(e) =>
                setForm({
                  ...form,
                  username:
                    e.target
                      .value,
                })
              }
            />

            <input
              placeholder="Phone"
              value={
                form.phone
              }
              onChange={(e) =>
                setForm({
                  ...form,
                  phone:
                    e.target
                      .value,
                })
              }
            />
          </>
        )}

        <input
          placeholder="Email"
          value={form.email}
          onChange={(e) =>
            setForm({
              ...form,
              email:
                e.target.value,
            })
          }
        />

        <input
          type="password"
          placeholder="Password"
          value={
            form.password
          }
          onChange={(e) =>
            setForm({
              ...form,
              password:
                e.target
                  .value,
            })
          }
        />

        <button
          type="submit"
        >
          {loading
            ? "Loading..."
            : "Submit"}
        </button>
      </form>
    </div>
  );
}