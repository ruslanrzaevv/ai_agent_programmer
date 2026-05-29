// src/pages/IncidentsPage.jsx

import {
  useState,
} from "react";

import useIncidents from "../hooks/useIncidents";

import IncidentCard from "../components/incidents/IncidentCard";
import IncidentFilters from "../components/incidents/IncidentFilters";
import Loading from "../components/common/Loading";

export default function IncidentsPage({
  onIncidentClick,
}) {

  const {
    incidents,
    loading,
  } = useIncidents();

  const [
    filter,
    setFilter,
  ] = useState("all");

  if (loading) {
    return <Loading />;
  }

  const filtered =
    filter === "all"
      ? incidents
      : incidents.filter(
          i =>
            i.status === filter ||
            i.severity === filter
        );

  return (

    <div
      style={{
        padding:
          "32px 36px",
      }}
    >

      <h1>
        Incidents
      </h1>

      <IncidentFilters
        filter={filter}
        setFilter={setFilter}
      />

      <div
        style={{
          display: "flex",
          flexDirection:
            "column",
          gap: 12,
        }}
      >

        {filtered.map(
          incident => (

            <IncidentCard
              key={
                incident.id
              }
              incident={
                incident
              }
              onClick={
                onIncidentClick
              }
            />

          )
        )}

      </div>

    </div>
  );
}