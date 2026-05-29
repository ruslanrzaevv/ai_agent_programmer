// src/components/layout/NotificationBell.jsx

export default function NotificationBell({
  count = 0,
}) {

  return (
    <div
      style={{
        position:
          "relative",

        cursor:
          "pointer",

        fontSize: 20,
      }}
    >

      🔔

      {count > 0 && (

        <span
          style={{
            position:
              "absolute",

            top: -6,

            right: -6,

            width: 18,

            height: 18,

            borderRadius:
              "50%",

            background:
              "#F43F5E",

            color:
              "white",

            display:
              "flex",

            alignItems:
              "center",

            justifyContent:
              "center",

            fontSize: 10,
          }}
        >
          {count}
        </span>

      )}

    </div>
  );
}