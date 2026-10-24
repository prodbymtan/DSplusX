/**
 * useStandby hook
 *
 * Manages the patient's "standby mode" lifecycle:
 * 1. Requests location permission
 * 2. Gets current position (one-shot — no continuous tracking)
 * 3. Registers standby session with the API
 * 4. Connects the WebSocket for real-time slot events
 * 5. Handles push notification foreground events
 */
import { useEffect, useRef, useState } from "react";
import * as Location from "expo-location";
import * as Notifications from "expo-notifications";
import { slotsApi } from "../services/api";
import { slotWebSocket, SlotEvent } from "../services/websocket";

export type StandbyStatus = "idle" | "active" | "error";

export function useStandby() {
  const [status, setStatus] = useState<StandbyStatus>("idle");
  const [currentLocation, setCurrentLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [liveSlotEvent, setLiveSlotEvent] = useState<SlotEvent | null>(null);
  const unsubscribeWsRef = useRef<(() => void) | null>(null);

  const activate = async (radiusMeters = 5000, durationSeconds = 7200) => {
    try {
      // Request foreground location permission
      const { status: perm } = await Location.requestForegroundPermissionsAsync();
      if (perm !== "granted") {
        setStatus("error");
        return { success: false, reason: "Location permission denied" };
      }

      // One-shot position — no background tracking (battery-friendly + privacy-safe)
      const position = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      const coords = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };
      setCurrentLocation(coords);

      // Register standby with the API
      await slotsApi.activateStandby(
        coords.lat,
        coords.lng,
        radiusMeters,
        durationSeconds
      );

      // Subscribe to real-time WebSocket events
      await slotWebSocket.connect();
      unsubscribeWsRef.current = slotWebSocket.subscribe((event) => {
        if (event.event === "slot_available") {
          setLiveSlotEvent(event);
        }
      });

      setStatus("active");
      return { success: true, coords };
    } catch (err) {
      setStatus("error");
      return { success: false, reason: String(err) };
    }
  };

  const deactivate = async () => {
    unsubscribeWsRef.current?.();
    slotWebSocket.disconnect();
    await slotsApi.deactivateStandby();
    setStatus("idle");
    setLiveSlotEvent(null);
  };

  // Listen for push notification taps (app in background/killed)
  useEffect(() => {
    const sub = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data as Record<string, string>;
      if (data?.event_type === "slot_available" && data?.slot_id) {
        setLiveSlotEvent({
          event: "slot_available",
          slot_id: data.slot_id,
          clinic_id: "",
          clinic_name: data.clinic_name ?? "Nearby Clinic",
          start_time: data.start_time ?? "",
          duration_minutes: parseInt(data.duration_minutes ?? "0", 10),
        });
      }
    });
    return () => sub.remove();
  }, []);

  return { status, currentLocation, liveSlotEvent, activate, deactivate };
}
