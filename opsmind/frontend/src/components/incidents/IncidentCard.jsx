// src/components/incidents/IncidentCard.jsx

import Card from "../common/Card";
import Badge from "../common/Badge";

import {
  SEV_CONFIG,
  STATUS_CONFIG,
} from "../../styles/constants";

import { timeAgo } from "../../utils/timeAgo";

export default function IncidentCard({
  incident,
  onClick,
}) {

  const sev =
    SEV_CONFIG[
      incident.severity
    ];

  const status =
    STATUS_CONFIG[
      incident.status
    ];

  return (

    <Card
      hoverable
      onClick={() =>
        onClick(
          incident
        )
      }
      style={{
        padding:
          "20px 24px",
      }}
    >

      <div
        style={{
          display:
            "flex",

          justifyContent:
            "space-between",
        }}
      >

        <div>

          <div
            style={{
              display:
                "flex",

              gap: 8,

              marginBottom: 8,
            }}
          >

            <Badge
              color={
                sev.color
              }
              glow={
                sev.glow
              }
              small
            >
              {
                sev.label
              }
            </Badge>

            <Badge
              color={
                status.color
              }
              small
            >
              {
                status.label
              }
            </Badge>

          </div>

          <div
            style={{
              fontSize: 15,
              fontWeight: 600,
            }}
          >
            {
              incident.title
            }
          </div>

          <div
            style={{
              marginTop: 6,
              fontSize: 12,
            }}
          >
            {
              incident.error_count
            } errors
            •
            {" "}
            {
              timeAgo(
                incident.started_at
              )
            }
          </div>

        </div>

      </div>

    </Card>

  );
}