// DupeClear Pro — Gumroad sale webhook -> generates a real DCP-XXXX license
// key (same HMAC scheme as core/license.py) and emails it to the buyer.
//
// Deploy with Wrangler. Required secrets (set via `wrangler secret put NAME`,
// never committed to the repo):
//   LICENSE_SECRET   hex string, the app's HMAC secret (from core/license.py _secret())
//   WEBHOOK_TOKEN     random string; must match the `token` query param on the
//                     Gumroad Ping URL so randoms can't hit this endpoint
//   RESEND_API_KEY    Resend API key used to send the license email
//
// Required vars (wrangler.toml [vars], not secret):
//   GUMROAD_PERMALINK product permalink, so we ignore Ping events for other
//                     Gumroad products on the same account
//   SENDER_EMAIL      "from" address for the license email (must be a
//                     verified sender/domain in Resend)

const DOMAIN = new TextEncoder().encode("DupeClearPro-v1-LICENSE");

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Not found", { status: 404 });
    }

    const url = new URL(request.url);
    if (url.searchParams.get("token") !== env.WEBHOOK_TOKEN) {
      return new Response("Forbidden", { status: 403 });
    }

    const form = await request.formData();
    const saleId = form.get("sale_id");
    const email = form.get("email");
    const permalink = form.get("product_permalink");
    const refunded = form.get("refunded") === "true";

    if (!saleId || !email) {
      return new Response("Missing sale_id or email", { status: 400 });
    }
    // Gumroad's Ping fires for every product on the account, not just this one.
    if (env.GUMROAD_PERMALINK && permalink !== env.GUMROAD_PERMALINK) {
      return new Response("Ignored: different product", { status: 200 });
    }
    if (refunded) {
      return new Response("Ignored: refund", { status: 200 });
    }

    // Idempotent: Gumroad may retry the Ping. Reuse the key already issued
    // for this sale instead of minting (and emailing) a second one.
    const existing = await env.LICENSES.get(saleId);
    let licenseKey;
    if (existing) {
      licenseKey = JSON.parse(existing).key;
    } else {
      licenseKey = await generateLicenseKey(env.LICENSE_SECRET);
      await env.LICENSES.put(saleId, JSON.stringify({
        email,
        key: licenseKey,
        created_at: new Date().toISOString(),
      }));
    }

    await sendLicenseEmail(env, email, licenseKey);
    return new Response("OK", { status: 200 });
  },
};

async function generateLicenseKey(secretHex) {
  const secret = hexToBytes(secretHex);
  const serial = crypto.getRandomValues(new Uint8Array(8));

  const data = new Uint8Array(DOMAIN.length + serial.length);
  data.set(DOMAIN, 0);
  data.set(serial, DOMAIN.length);

  const cryptoKey = await crypto.subtle.importKey(
    "raw", secret, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const macBuf = await crypto.subtle.sign("HMAC", cryptoKey, data);
  const mac = new Uint8Array(macBuf).slice(0, 8);

  const serialHex = bytesToHex(serial).toUpperCase();
  const macHex = bytesToHex(mac).toUpperCase();
  return `DCP-${serialHex.slice(0, 8)}-${serialHex.slice(8, 16)}-${macHex.slice(0, 8)}-${macHex.slice(8, 16)}`;
}

function hexToBytes(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
  }
  return bytes;
}

function bytesToHex(bytes) {
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function sendLicenseEmail(env, to, licenseKey) {
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: env.SENDER_EMAIL,
      to,
      subject: "Your DupeClear Pro license key",
      text:
        "Thanks for purchasing DupeClear Pro!\n\n" +
        `Your license key:\n${licenseKey}\n\n` +
        "To activate:\n" +
        "1. Open DupeClear Pro\n" +
        "2. Go to Settings -> License\n" +
        "3. Paste the key above and click Activate\n\n" +
        "Note: the key binds to the first machine you activate it on.\n\n" +
        "Questions? Contact support@esupplytech.com.",
    }),
  });
  if (!res.ok) {
    throw new Error(`Resend API error: ${res.status} ${await res.text()}`);
  }
}
