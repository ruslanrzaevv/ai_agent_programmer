// src/components/system/HealthCard.jsx

export default function HealthCard({
    title,
    value,
   }) {
   
    return (
     <div
      style={{
       background:
         "#0D1220",
   
       padding: 20,
   
       borderRadius: 12,
      }}
     >
      <h3>
       {title}
      </h3>
   
      <h2>
       {value}
      </h2>
     </div>
    );
   }