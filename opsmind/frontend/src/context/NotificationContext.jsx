// src/context/NotificationContext.jsx

import {
    createContext,
    useContext,
    useState,
  } from "react";
  
  const NotificationContext =
    createContext();
  
  export function NotificationProvider({
    children,
  }) {
  
    const [
      notifications,
      setNotifications,
    ] = useState([]);
  
    function addNotification(
      notification
    ) {
  
      const id =
        Date.now();
  
      setNotifications(
        (prev) => [
          {
            id,
            ...notification,
          },
          ...prev,
        ]
      );
  
      setTimeout(() => {
  
        setNotifications(
          (prev) =>
            prev.filter(
              (n) =>
                n.id !== id
            )
        );
  
      }, 5000);
    }
  
    function removeNotification(
      id
    ) {
  
      setNotifications(
        (prev) =>
          prev.filter(
            (n) =>
              n.id !== id
          )
      );
    }
  
    return (
      <NotificationContext.Provider
        value={{
          notifications,
          addNotification,
          removeNotification,
        }}
      >
        {children}
      </NotificationContext.Provider>
    );
  }
  
  export function useNotifications() {
    return useContext(
      NotificationContext
    );
  }
