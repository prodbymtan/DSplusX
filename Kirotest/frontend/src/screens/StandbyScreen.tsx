/**
 * Standby Screen
 *
 * The core patient UX — the "Go Online" button that activates geofenced
 * standby mode and presents real-time slot alerts with a countdown timer.
 */
import React, { useEffect, useRef, useState } from "react";
import {
  Alert,
  Animated,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useStandby } from "../hooks/useStandby";
import { bookingsApi, Slot, slotsApi } from "../services/api";
import { SlotAlertCard } from "../components/SlotAlertCard";

export default function StandbyScreen() {
  const { status, currentLocation, liveSlotEvent, activate, deactivate } =
    useStandby();

  const [nearbySlots, setNearbySlots] = useState<Slot[]>([]);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  // Pulse animation when standby is active
  useEffect(() => {
    if (status === "active") {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.15,
            duration: 800,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [status]);

  // Fetch nearby slots when location is set
  useEffect(() => {
    if (currentLocation) {
      slotsApi
        .getNearby(currentLocation.lat, currentLocation.lng)
        .then(({ data }) => setNearbySlots(data))
        .catch(console.error);
    }
  }, [currentLocation]);

  const handleToggleStandby = async () => {
    if (status === "active") {
      await deactivate();
      setNearbySlots([]);
    } else {
      const result = await activate();
      if (!result.success) {
        Alert.alert("Location Required", result.reason ?? "Enable location to use standby mode.");
      }
    }
  };

  const handleClaimSlot = async (slotId: string) => {
    try {
      const { data } = await bookingsApi.claim(slotId);
      // Show confirmation modal with countdown
      Alert.alert(
        "⚡ Slot Held — Confirm Now",
        `You have ${data.expires_in_seconds} seconds to confirm your booking at this clinic.`,
        [
          {
            text: "Confirm Booking",
            onPress: () => confirmSlot(slotId),
            style: "default",
          },
          { text: "Cancel", style: "cancel" },
        ]
      );
    } catch (err: any) {
      Alert.alert(
        "Slot Taken",
        err.response?.data?.detail ?? "Someone else claimed this slot first. Keep standby on for the next one."
      );
    }
  };

  const confirmSlot = async (slotId: string) => {
    try {
      await bookingsApi.confirm(slotId);
      Alert.alert("✅ Booking Confirmed!", "You're all set. See you at the clinic!");
      await deactivate();
    } catch (err: any) {
      Alert.alert("Confirmation Failed", err.response?.data?.detail ?? "Your hold expired.");
    }
  };

  const isActive = status === "active";

  return (
    <View style={styles.container}>
      {/* Header */}
      <Text style={styles.title}>HealthSlot</Text>
      <Text style={styles.subtitle}>
        {isActive
          ? "You're on standby. We'll alert you the instant a slot opens nearby."
          : "Tap to go on standby and claim same-day appointments near you."}
      </Text>

      {/* Standby toggle button */}
      <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
        <TouchableOpacity
          style={[styles.standbyButton, isActive && styles.standbyButtonActive]}
          onPress={handleToggleStandby}
          activeOpacity={0.85}
        >
          <Text style={styles.standbyButtonIcon}>{isActive ? "⏸" : "▶"}</Text>
          <Text style={styles.standbyButtonLabel}>
            {isActive ? "Go Offline" : "Go on Standby"}
          </Text>
        </TouchableOpacity>
      </Animated.View>

      {/* Live slot alert — pushed from WebSocket or push notification */}
      {liveSlotEvent && isActive && (
        <SlotAlertCard
          event={liveSlotEvent}
          onClaim={() => handleClaimSlot(liveSlotEvent.slot_id)}
          countdownSeconds={60}
        />
      )}

      {/* Nearby available slots */}
      {isActive && nearbySlots.length > 0 && (
        <View style={styles.nearbySection}>
          <Text style={styles.sectionTitle}>
            {nearbySlots.length} Available Slots Nearby
          </Text>
          {nearbySlots.slice(0, 5).map((slot) => (
            <TouchableOpacity
              key={slot.id}
              style={styles.slotRow}
              onPress={() => handleClaimSlot(slot.id)}
            >
              <View>
                <Text style={styles.slotClinic}>{slot.clinic_name}</Text>
                <Text style={styles.slotProvider}>{slot.provider_name}</Text>
                <Text style={styles.slotTime}>
                  {new Date(slot.start_time).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}{" "}
                  · {slot.duration_minutes} min
                </Text>
              </View>
              <View style={styles.distanceBadge}>
                <Text style={styles.distanceText}>
                  {slot.distance_meters
                    ? `${Math.round(slot.distance_meters / 100) / 10} km`
                    : "Nearby"}
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F0F4FF",
    alignItems: "center",
    paddingTop: 80,
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: "800",
    color: "#1A2E5A",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: "#6B7280",
    textAlign: "center",
    lineHeight: 22,
    marginBottom: 48,
  },
  standbyButton: {
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    elevation: 8,
    borderWidth: 3,
    borderColor: "#E5E7EB",
  },
  standbyButtonActive: {
    backgroundColor: "#1A2E5A",
    borderColor: "#3B82F6",
  },
  standbyButtonIcon: {
    fontSize: 40,
    marginBottom: 8,
  },
  standbyButtonLabel: {
    fontSize: 15,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  nearbySection: {
    width: "100%",
    marginTop: 32,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#6B7280",
    marginBottom: 12,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  slotRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  slotClinic: { fontSize: 15, fontWeight: "700", color: "#1A2E5A" },
  slotProvider: { fontSize: 13, color: "#6B7280", marginTop: 2 },
  slotTime: { fontSize: 13, color: "#3B82F6", marginTop: 4, fontWeight: "500" },
  distanceBadge: {
    backgroundColor: "#EFF6FF",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
  },
  distanceText: { fontSize: 12, fontWeight: "600", color: "#3B82F6" },
});
