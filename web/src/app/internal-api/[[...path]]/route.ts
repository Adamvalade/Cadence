import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
]);

function upstreamBase(): string {
  const explicit = (process.env.API_URL || "").trim().replace(/\/$/, "");
  if (explicit) return explicit;
  const pub = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");
  if (pub.endsWith("/api")) return "http://api:8000/api";
  if (pub.startsWith("http://") || pub.startsWith("https://")) return pub;
  return "http://127.0.0.1:8000";
}

function forwardRequestHeaders(req: NextRequest): Headers {
  const h = new Headers();
  for (const name of ["authorization", "content-type", "cookie", "accept"]) {
    const v = req.headers.get(name);
    if (v) h.set(name, v);
  }
  return h;
}

function forwardResponseHeaders(src: Headers): Headers {
  const h = new Headers();
  src.forEach((value, key) => {
    const lk = key.toLowerCase();
    if (HOP_BY_HOP.has(lk) || lk === "content-encoding" || lk === "content-length") return;
    h.append(key, value);
  });
  return h;
}

type Ctx = { params: Promise<{ path?: string[] }> };

async function proxy(req: NextRequest, ctx: Ctx): Promise<NextResponse> {
  const { path } = await ctx.params;
  const subpath = path?.join("/") ?? "";
  const targetUrl = `${upstreamBase()}/${subpath}${req.nextUrl.search}`;

  const headers = forwardRequestHeaders(req);
  const init: RequestInit & { duplex?: "half" } = {
    method: req.method,
    headers,
    redirect: "manual",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = req.body;
    init.duplex = "half";
  }

  const upstreamRes = await fetch(targetUrl, init);
  const outHeaders = forwardResponseHeaders(upstreamRes.headers);
  return new NextResponse(upstreamRes.body, {
    status: upstreamRes.status,
    statusText: upstreamRes.statusText,
    headers: outHeaders,
  });
}

export async function GET(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx);
}

export async function POST(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx);
}

export async function PUT(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx);
}

export async function PATCH(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx);
}

export async function DELETE(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx);
}

export async function HEAD(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx);
}

export async function OPTIONS(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx);
}
