import {
    useMemo,
   } from "react";
   
   export default function useStats(
    incidents
   ) {
   
    return useMemo(
     () => {
   
      const open =
       incidents.filter(
         i =>
         i.status !==
         "resolved"
       );
   
      const critical =
       incidents.filter(
         i =>
         i.severity ===
         "critical"
       );
   
      return {
   
       open:
        open.length,
   
       critical:
        critical.length,
   
       total:
        incidents.length,
   
      };
   
     },
   
     [incidents]
    );
   }