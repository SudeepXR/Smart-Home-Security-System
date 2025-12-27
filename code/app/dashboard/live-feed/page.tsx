"use client";

import { useSearchParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import {IP_MEG} from "../../lib/config";
type CameraKey = "cam1" | "cam2" | "cam3" | "cam4";

export default function LiveFeedPage() {   // ← FIXED (no JSX.Element)
  const searchParams = useSearchParams();
  const rawCamera = searchParams?.get("camera") ?? "cam1";
  const cameraId = (rawCamera as CameraKey) ?? "cam1";

  const [isStarting, setIsStarting] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState<boolean>(false);

  const imgRef = useRef<HTMLImageElement | null>(null);

  const cameraNames = {
    cam1: "Front Door",
    cam2: "Backyard",
    cam3: "Living Room",
    cam4: "Garage",
  } as const;

  const backendURL = IP_MEG;

  /*useEffect(() => {
    let cancelled = false;

    async function startFeed() {
      setError(null);
      setIsStarting(true);

      try {
        const res = await fetch(`${backendURL}/feed`);
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`Backend error ${res.status}: ${text}`);
        }

        if (!cancelled) {
          if (imgRef.current) imgRef.current.src = `${backendURL}/feed`;
          setIsLive(true);
          setIsStarting(false);
        }
      } catch (err: any) {
        setError(String(err.message ?? err));
        setIsStarting(false);
        setIsLive(false);
      }
    }

    startFeed();
    return () => {
      cancelled = true;
    };
  }, [cameraId, backendURL]);*/

  async function stopFeed() {
    try {
      setIsStarting(true);
      await fetch(`${backendURL}/stop_feed`, { method: "POST" });
      if (imgRef.current) imgRef.current.src = "";
      setIsLive(false);
      setIsStarting(false);
    } catch (err) {
      setError(String(err));
      setIsStarting(false);
    }
  }

  async function restartFeed() {
    setError(null);
    setIsStarting(true);
    try {
      await fetch(`${backendURL}/feed`, { method: "POST" }); //this api was /stop-feed if something dies, change
    } catch {}
    setTimeout(() => {
      if (imgRef.current) imgRef.current.src = `${backendURL}/feed?t=${Date.now()}`;
      setIsStarting(false);
      setIsLive(true);
    }, 300);
  }

  return (
    <div className="p-8 space-y-6">

      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="p-2 hover:bg-card rounded-lg transition">
          <ArrowLeft className="w-6 h-6 text-foreground" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-foreground">Live Feed</h1>
          <p className="text-muted-foreground">{cameraNames[cameraId]}</p>
        </div>

        <div className="ml-auto flex gap-2">
          <button
            onClick={restartFeed}
            className="bg-primary text-primary-foreground px-3 py-1 rounded-md"
          >
            Start
          </button>
          <button
            onClick={stopFeed}
            className="bg-destructive text-destructive-foreground px-3 py-1 rounded-md"
          >
            Stop
          </button>
        </div>
      </div>

      <div className="glass rounded-2xl overflow-hidden relative">
        <div className="bg-secondary/50 aspect-video lg:h-[600px] flex items-center justify-center relative">
          {error && (
            <div className="p-4 text-center">
              <p className="text-red-500 font-semibold">{error}</p>
            </div>
          )}

          {isStarting && !error && (
            <p className="text-muted-foreground text-lg animate-pulse">
              Starting camera, please wait...
            </p>
          )}

          {!isStarting && !error && (
            <img
              ref={imgRef}
              src={`${backendURL}/feed`}
              alt="Live camera"
              className="object-contain w-full h-full"
            />
          )}

          {!isStarting && !error && isLive && (
            <div className="absolute top-4 right-4 flex items-center gap-2 bg-destructive/20 px-3 py-1.5 rounded-full">
              <div className="w-2 h-2 bg-destructive rounded-full animate-pulse"></div>
              <span className="text-xs text-destructive font-semibold">REC</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
