export default function OrbitAnalysisCard({
    incident,
  }) {
    return (
      <div className="card">
        <h3>🛰 Orbit Analysis</h3>
        <div>
          <strong>Root Cause</strong>
          <p>{incident.orbit_root_cause}</p>
        </div>
      
        <div>
          <strong>Risk Score</strong>
          <p>{incident.orbit_risk_score}/100</p>
        </div>
  
        <div>
          <strong>Blast Radius</strong>
          <p>{incident.orbit_blast_radius}</p>
        </div>
  
        <div>
          <strong>Definitions</strong>
          <p>{incident.orbit_definitions}</p>
        </div>
  
        <div>
          <strong>Imports</strong>
          <p>{incident.orbit_imports}</p>
        </div>
  
        <div>
          <strong>Affected Services</strong>
  
          {incident.orbit_affected_services?.map(
            (x) => (
              <span key={x}>
                {x}
              </span>
            )
          )}
        </div>
  
        <div>
          <strong>Affected Files</strong>
  
          {incident.orbit_affected_files?.map(
            (x) => (
              <div key={x}>
                {x}
              </div>
            )
          )}
        </div>
      </div>
    )
  }