// src/pages/SettingsPage.jsx

import useAuth
from "../hooks/useAuth";

export default function SettingsPage() {

  const {
    user,
    logout,
  } = useAuth();

  return (

    <div
      style={{
        padding:
          "32px 36px",
      }}
    >

      <h1>
        Settings
      </h1>

      <div>
        {user?.email}
      </div>

      <button
        onClick={logout}
      >
        Logout
      </button>

    </div>

  );
}