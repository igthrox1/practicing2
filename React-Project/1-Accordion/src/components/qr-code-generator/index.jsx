import { useState } from "react";
import {QRCode} from "react-qr-code";

function QRCodeGenerator() {
  const [qrCode, setQrCode] = useState("");
  const [input, setInput] = useState("");

  function handleGenerateQrCode() {
    setQrCode(input);
    setInput('')
  }

  return (
    <>
      <div>
        <h1>QR Code Generator</h1>
        <div>
          <input
            onChange={(e) => setInput(e.target.value)}
            type="text"
            name="qr-code"
            placeholder="Enter your Value here"
            value={input}
          />
          <button
            disabled={input && input.trim() !== "" ? false : true}
            onClick={handleGenerateQrCode}
          >
            Generate
          </button>
        </div>
        <QRCode id="qr-code-value" value={qrCode} size={400} bgColor="#fff" />
      </div>
    </>
  );
}

export default QRCodeGenerator;
