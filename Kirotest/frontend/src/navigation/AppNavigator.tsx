/**
 * Root navigation — switches between Auth and Patient stacks
 * based on Zustand auth state.
 */
import React, { useEffect } from "react";
import { ActivityIndicator, View } from "react-native";
import { useAuthStore } from "../store/authStore";
import LoginScreen from "../screens/LoginScreen";
import StandbyScreen from "../screens/StandbyScreen";

export default function AppNavigator() {
  const { user, isLoading, restoreSession } = useAuthStore();

  useEffect(() => {
    restoreSession();
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#1A2E5A" />
      </View>
    );
  }

  // Simple stack: unauthenticated → Login, authenticated → Standby
  // In a full app, replace with Expo Router or React Navigation stack
  return user ? <StandbyScreen /> : <LoginScreen />;
}
