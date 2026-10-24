/**
 * SlotAlertCard — the "Uber surge" moment of the app.
 *
 * Shown as an urgent overlay when a real-time slot event arrives
 * via WebSocket or push notification. Features a live countdown timer.
 */
import React, { useEffect, useState } from "react";
import {
  Animated,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SlotEvent } from "../services/websocket";
import { format } from "date-fns";

interface Props {
  event: SlotEvent;
  onClaim: () => void;
  countdownSeconds: number;
}

export function SlotAlertCard({ event, onClaim, countdownSeconds }: Props) {
  const [secondsLeft, setSecondsLeft] = useState(countdownSeconds);
  const flashAnim = React.useRef(new Animated.Value(1)).current;

  // Countdown timer
  useEffect(() => {
    if (secondsLeft <= 0) return;
    const timer = setInterval(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearInterval(timer);
  }, [secondsLeft]);

  // Flash red when under 10 seconds
  useEffect(() => {
    if (secondsLeft <= 10 && secondsLeft > 0) {
      Animated.sequence([
        Animated.timing(flashAnim, { toValue: 0.4, duration: 200, useNativeDriver: true }),
        Animated.timing(flashAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
      ]).start();
    }
  }, [secondsLeft]);

  const isExpired = secondsLeft <= 0;
  const isUrgent = secondsLeft <= 10;

  const formattedTime = event.start_time
    ? format(new Date(event.start_time), "h:mm a")
    : "—";

  return (
    <Animated.View
      style={[
        styles.card,
        isUrgent && styles.cardUrgent,
        { opacity: isExpired ? 0.5 : flashAnim },
      ]}
    >
      {/* Urgency header */}
      <View style={styles.header}>
        <Text style={styles.headerEmoji}>⚡</Text>
        <Text style={styles.headerText}>SLOT JUST OPENED</Text>
        <View style={[styles.countdown, isUrgent && styles.countdownUrgent]}>
          <Text style={[styles.countdownText, isUrgent && styles.countdownTextUrgent]}>
            {isExpired ? "EXPIRED" : `${secondsLeft}s`}
          </Text>
        </View>
      </View>

      {/* Slot details */}
      <View style={styles.details}>
        <Text style={styles.clinicName}>{event.clinic_name}</Text>
        <Text style={styles.slotInfo}>
          {formattedTime} · {event.duration_minutes} min appointment
        </Text>
      </View>

      {/* Claim button */}
      <TouchableOpacity
        style={[styles.claimButton, isExpired && styles.claimButtonDisabled]}
        onPress={onClaim}
        disabled={isExpired}
        activeOpacity={0.8}
      >
        <Text style={styles.claimButtonText}>
          {isExpired ? "Slot Expired" : "Claim This Slot →"}
        </Text>
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: "100%",
    backgroundColor: "#1A2E5A",
    borderRadius: 20,
    padding: 20,
    marginTop: 32,
    shadowColor: "#1A2E5A",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 12,
  },
  cardUrgent: {
    backgroundColor: "#DC2626",
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
  },
  headerEmoji: { fontSize: 20, marginRight: 8 },
  headerText: {
    flex: 1,
    fontSize: 12,
    fontWeight: "800",
    color: "#93C5FD",
    letterSpacing: 1.5,
    textTransform: "uppercase",
  },
  countdown: {
    backgroundColor: "rgba(255,255,255,0.15)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  countdownUrgent: { backgroundColor: "rgba(255,255,255,0.3)" },
  countdownText: { fontSize: 14, fontWeight: "800", color: "#FFFFFF" },
  countdownTextUrgent: { color: "#FEF2F2" },
  details: { marginBottom: 20 },
  clinicName: {
    fontSize: 22,
    fontWeight: "800",
    color: "#FFFFFF",
    marginBottom: 4,
  },
  slotInfo: { fontSize: 15, color: "#93C5FD" },
  claimButton: {
    backgroundColor: "#3B82F6",
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
  },
  claimButtonDisabled: { backgroundColor: "#6B7280" },
  claimButtonText: { fontSize: 17, fontWeight: "700", color: "#FFFFFF" },
});
