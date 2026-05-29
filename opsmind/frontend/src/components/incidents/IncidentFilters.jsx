// src/components/incidents/IncidentFilters.jsx

export default function IncidentFilters({
    filter,
    setFilter,
  }) {
  
    const filters = [
      "all",
      "critical",
      "high",
      "medium",
      "open",
      "resolved",
    ];
  
    return (
  
      <div
        style={{
          display:
            "flex",
  
          gap: 8,
  
          marginBottom:
            20,
        }}
      >
  
        {filters.map(
          (item) => (
  
            <button
              key={item}
  
              onClick={() =>
                setFilter(
                  item
                )
              }
            >
              {item}
            </button>
  
          )
        )}
  
      </div>
  
    );
  }