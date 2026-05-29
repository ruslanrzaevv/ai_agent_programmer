// src/components/incidents/IncidentReplay.jsx

import {
    useEffect,
    useRef,
    useState,
  } from "react";
  
  export default function IncidentReplay(
    {
     incident,
     onClose,
    }
    ) {
  
    const timeline =
      incident.timeline || [];
  
    const [currentIndex,
      setCurrentIndex] =
      useState(0);
  
    const [playing,
      setPlaying] =
      useState(false);
  
    const intervalRef =
      useRef(null);
  
    const current =
      timeline[
        currentIndex
      ];
  
    useEffect(() => {
  
      if (!playing)
        return;
  
      intervalRef.current =
        setInterval(() => {
  
          setCurrentIndex(
            (prev) => {
  
              if (
                prev >=
                timeline.length - 1
              ) {
  
                setPlaying(
                  false
                );
  
                return prev;
              }
  
              return prev + 1;
            }
          );
  
        }, 1000);
  
      return () =>
        clearInterval(
          intervalRef.current
        );
  
    }, [
      playing,
      timeline.length,
    ]);
  
    return (
      <div
        style={{
          position:
            "fixed",
  
          inset: 0,
  
          background:
            "rgba(0,0,0,.85)",
  
          display:
            "flex",
  
          justifyContent:
            "center",
  
          alignItems:
            "center",
  
          zIndex: 999,
        }}
      >
        <div
          style={{
            width: 800,
  
            background:
              "#0D1220",
  
            borderRadius: 12,
  
            padding: 30,
          }}
        >
          <h2>
            Incident Replay
          </h2>
  
          <h3>
            {
              incident.title
            }
          </h3>
  
          <button
            onClick={
              onClose
            }
          >
            Close
          </button>
  
          <hr />
  
          {current && (
            <>
              <h3>
                +{
                  current.minute
                }
                min
              </h3>
  
              <p>
                Event:
                {" "}
                {
                  current.event
                }
              </p>
  
              <p>
                Errors:
                {" "}
                {
                  current.error_count
                }
              </p>
  
              <p>
                CPU:
                {" "}
                {
                  current.cpu_percent
                }
                %
              </p>
            </>
          )}
  
          <input
            type="range"
            min={0}
            max={
              timeline.length - 1
            }
            value={
              currentIndex
            }
            onChange={(e) =>
              setCurrentIndex(
                Number(
                  e.target.value
                )
              )
            }
            style={{
              width: "100%",
              marginTop: 20,
            }}
          />
  
          <div
            style={{
              marginTop: 20,
            }}
          >
            <button
              onClick={() =>
                setPlaying(
                  !playing
                )
              }
            >
              {playing
                ? "Pause"
                : "Play"}
            </button>
  
            <button
              onClick={() =>
                setCurrentIndex(
                  0
                )
              }
            >
              Reset
            </button>
          </div>
        </div>
      </div>
    );
  }