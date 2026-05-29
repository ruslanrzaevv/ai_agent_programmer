// src/pages/SystemDashboard.jsx

import useHealth
from "../hooks/useHealth";

import HealthCard
from "../components/system/HealthCard";

export default function SystemDashboard() {

 const health =
  useHealth();

 if (!health) {
  return null;
 }

 return (
  <div
   style={{
    padding:32,
   }}
  >

   <h1>
    Infrastructure
   </h1>

   <div
    style={{
     display:"flex",
     gap:20,
    }}
   >

    <HealthCard
     title="Redis"
     value={
      health.redis
     }
    />

    <HealthCard
     title="Status"
     value={
      health.status
     }
    />

   </div>

  </div>
 );
}