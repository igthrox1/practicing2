import React, { useState, useEffect } from "react";

const OrderBookDisplay = () => {
  const [binanceData, setBinanceData] = useState({ bid: null, ask: null });
  const [bybitData, setBybitData] = useState({ bid: null, ask: null });
  const [binanceStatus, setBinanceStatus] = useState("Connecting...");
  const [bybitStatus, setBybitStatus] = useState("Connecting...");

  useEffect(() => {
    // Binance Testnet WebSocket (CORRECT ENDPOINT)
    const binanceWs = new WebSocket(
      "wss://stream.binancefuture.com/stream?streams=btcusdt@bookTicker"
    );

    binanceWs.onopen = () => setBinanceStatus("Connected");
    binanceWs.onerror = () => setBinanceStatus("Error");
    binanceWs.onclose = () => setBinanceStatus("Disconnected");

    binanceWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.data) {
        setBinanceData({
          bid: parseFloat(data.data.b),
          ask: parseFloat(data.data.a),
        });
      }
    };

    // Bybit Mainnet WebSocket (for demo trading market data)
    const bybitWs = new WebSocket("wss://stream.bybit.com/v5/public/linear");

    bybitWs.onopen = () => {
      setBybitStatus("Connected");
      bybitWs.send(
        JSON.stringify({
          op: "subscribe",
          args: ["tickers.BTCUSDT"],
        })
      );
    };

    bybitWs.onerror = () => setBybitStatus("Error");
    bybitWs.onclose = () => setBybitStatus("Disconnected");

    bybitWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.data && data.data.bid1Price && data.data.ask1Price) {
        setBybitData({
          bid: parseFloat(data.data.bid1Price),
          ask: parseFloat(data.data.ask1Price),
        });
      }
    };

    return () => {
      binanceWs.close();
      bybitWs.close();
    };
  }, []);

  const formatPrice = (price) => {
    return price
      ? price.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      : "---";
  };

  const getSpread = (bid, ask) => {
    if (!bid || !ask) return "---";
    return (((ask - bid) / bid) * 100).toFixed(3) + "%";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            ⚡ Live Order Book Monitor
          </h1>
          <p className="text-gray-400">BTC/USDT Best Bid & Ask</p>
        </div>

        {/* Order Book Table */}
        <div className="bg-gray-800 rounded-lg shadow-2xl overflow-hidden border border-gray-700">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-700">
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                  Exchange
                </th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-gray-300">
                  Status
                </th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-green-400">
                  ↗ Best Bid
                </th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-red-400">
                  ↘ Best Ask
                </th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-300">
                  Spread
                </th>
              </tr>
            </thead>
            <tbody>
              {/* Binance Row */}
              <tr className="border-t border-gray-700 hover:bg-gray-750 transition-colors">
                <td className="px-6 py-5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-yellow-500 rounded-lg flex items-center justify-center">
                      <span className="text-black font-bold text-sm">BN</span>
                    </div>
                    <div>
                      <div className="text-white font-semibold">Binance</div>
                      <div className="text-xs text-gray-400">Testnet</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-5 text-center">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                      binanceStatus === "Connected"
                        ? "bg-green-900 text-green-300"
                        : "bg-red-900 text-red-300"
                    }`}
                  >
                    {binanceStatus}
                  </span>
                </td>
                <td className="px-6 py-5 text-right">
                  <div className="text-green-400 font-mono text-lg font-semibold">
                    ${formatPrice(binanceData.bid)}
                  </div>
                </td>
                <td className="px-6 py-5 text-right">
                  <div className="text-red-400 font-mono text-lg font-semibold">
                    ${formatPrice(binanceData.ask)}
                  </div>
                </td>
                <td className="px-6 py-5 text-right">
                  <div className="text-gray-300 font-mono text-sm">
                    {getSpread(binanceData.bid, binanceData.ask)}
                  </div>
                </td>
              </tr>

              {/* Bybit Row */}
              <tr className="border-t border-gray-700 hover:bg-gray-750 transition-colors">
                <td className="px-6 py-5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-sm">BB</span>
                    </div>
                    <div>
                      <div className="text-white font-semibold">Bybit</div>
                      <div className="text-xs text-gray-400">Demo</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-5 text-center">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                      bybitStatus === "Connected"
                        ? "bg-green-900 text-green-300"
                        : "bg-red-900 text-red-300"
                    }`}
                  >
                    {bybitStatus}
                  </span>
                </td>
                <td className="px-6 py-5 text-right">
                  <div className="text-green-400 font-mono text-lg font-semibold">
                    ${formatPrice(bybitData.bid)}
                  </div>
                </td>
                <td className="px-6 py-5 text-right">
                  <div className="text-red-400 font-mono text-lg font-semibold">
                    ${formatPrice(bybitData.ask)}
                  </div>
                </td>
                <td className="px-6 py-5 text-right">
                  <div className="text-gray-300 font-mono text-sm">
                    {getSpread(bybitData.bid, bybitData.ask)}
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Info Footer */}
        <div className="mt-6 text-center text-gray-500 text-sm">
          <p>Real-time order book data • Updates streaming via WebSocket</p>
          <p className="mt-1">
            Binance uses testnet data • Bybit uses mainnet public data for demo
            trading
          </p>
        </div>
      </div>
    </div>
  );
};

export default OrderBookDisplay;
