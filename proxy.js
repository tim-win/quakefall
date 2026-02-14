// WebSocket-to-UDP proxy for ioquake3
// Browser (WebSocket) <-> This proxy <-> Q3 Server (UDP)

const dgram = require('dgram');
const { WebSocketServer } = require('ws');

const WS_PORT = 27961;          // Port browser connects to via WebSocket
const Q3_HOST = '127.0.0.1';    // Q3 dedicated server address
const Q3_PORT = 27960;          // Q3 dedicated server UDP port

const wss = new WebSocketServer({ port: WS_PORT });
console.log(`WebSocket proxy listening on ws://0.0.0.0:${WS_PORT}`);
console.log(`Forwarding to Q3 server at ${Q3_HOST}:${Q3_PORT} (UDP)`);

wss.on('connection', (ws, req) => {
    console.log(`New browser client connected from ${req.socket.remoteAddress}`);

    // Create a UDP socket for this browser client
    const udp = dgram.createSocket('udp4');

    // Browser -> WebSocket -> UDP -> Q3 Server
    ws.on('message', (data) => {
        const buf = Buffer.from(data);
        console.log(`[WS->UDP] ${buf.length} bytes, first 20: ${buf.slice(0, 20).toString('hex')}`);
        udp.send(buf, Q3_PORT, Q3_HOST);
    });

    // Q3 Server -> UDP -> WebSocket -> Browser
    udp.on('message', (msg) => {
        console.log(`[UDP->WS] ${msg.length} bytes, first 20: ${msg.slice(0, 20).toString('hex')}`);
        if (ws.readyState === ws.OPEN) {
            ws.send(msg);
        }
    });

    // Cleanup on disconnect
    ws.on('close', () => {
        console.log('Browser client disconnected');
        udp.close();
    });

    ws.on('error', (err) => {
        console.error('WebSocket error:', err.message);
        udp.close();
    });

    udp.on('error', (err) => {
        console.error('UDP error:', err.message);
        ws.close();
    });
});
