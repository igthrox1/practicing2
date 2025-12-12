import { useState } from "react";
import "./index.css";

function RandomColor() {
  const [typeOf, setTypeOf] = useState("hex");
  const [color, setColor] = useState("black");

  const randomColorUtility = (Length) => {
    return Math.floor(Math.random() * Length);
  };

  const handleCreateHexRandomColor = () => {
    const hex = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, "A", "B", "C", "D", "E", "F"];
    let hexColor = "#";

    for (let i = 0; i < 6; i++) {
      hexColor += hex[randomColorUtility(hex.length)];
    }
    setColor(hexColor);
  };

  const handleCreateRandomRgbColor = () => {
    const r = randomColorUtility(256);
    const g = randomColorUtility(256);
    const b = randomColorUtility(256);

    setColor(`rgb(${r},${g},${b})`);
  };

  return (
    <>
      <div
        className="container"
        style={{
          width: "100vw",
          height: "100vh",
          backgroundColor: color,
        }}
      >
        <div className="btns">
          <button className="btn" onClick={() => setTypeOf("rgb")}>
            {" "}
            Create RGB button{" "}
          </button>
          <button className="btn" onClick={() => setTypeOf("hex")}>
            {" "}
            Create Hex Color{" "}
          </button>
          <button
            className="btn"
            onClick={
              typeOf === "hex"
                ? handleCreateHexRandomColor
                : handleCreateRandomRgbColor
            }
          >
            {" "}
            Generate Random Color{" "}
          </button>
        </div>

        <div className="color-txt">
          <h3>{typeOf === "rgb" ? "RGB Color" : "HEX Color"}</h3>
          <h1>{color}</h1>
        </div>
      </div>
    </>
  );
}

export default RandomColor;
