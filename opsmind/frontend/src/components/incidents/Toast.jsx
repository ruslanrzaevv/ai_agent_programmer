// src/components/incidents/Toast.jsx

export default function Toast({
    incident,
   }) {
   
    return (
   
     <div
      style={{
       position:"fixed",
   
       right:20,
   
       top:20,
   
       background:"#F43F5E",
   
       color:"white",
   
       padding:20,
   
       borderRadius:12,
      }}
     >
   
      <h3>
       New Incident
      </h3>
   
      <p>
       {
         incident.title
       }
      </p>
   
     </div>
   
    );
   
   }