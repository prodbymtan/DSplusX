# Relay design rules (apply to every UI task)

This is a React Native (Expo) app. Use StyleSheet, React Native components,
react-native-reanimated for animation, and react-native-svg for charts/rings.

## Direction: "Clinical calm, quietly alive"
Trustworthy like a good hospital, polished like a premium app.
Calm by default; motion only where it means something.

## Banned
- Purple, violet, or rainbow gradients. No gradients unless subtle and single-hue.
- Default system look: plain gray cards, generic centered layouts, identical card grids.
- Emoji as icons. Neon glows. Heavy shadows everywhere.

## Color (define once in src/theme/colors.ts and import everywhere)
- background: #FAF8F5 (warm off-white)   surface: #FFFFFF
- ink (text): #0F1B2D                    muted: #5B6575
- primary: #0E7C7B (deep teal: actions, links)
- accent: #E8664F (warm coral: live offer, Claim button, urgent moments only)
- amber: #D99A2B (countdowns)            sage: #DDEBE3 (calm backgrounds)
- Every text/background pair must meet WCAG AA contrast. Never use color alone to carry meaning.

## Typography (load with expo-font via @expo-google-fonts packages)
- Headings: Fraunces 600
- Body: IBM Plex Sans 400/500/600
- Numbers and vitals: IBM Plex Mono 500
- Big, confident type for key numbers (heart rate, days until renewal).
- Support Dynamic Type: don't disable font scaling.

## Motion (react-native-reanimated)
- Purposeful only:
  - Heart-rate line draws itself in when vitals load.
  - New offer card springs up from the bottom with one soft pulse.
  - Claim countdown is a ring that depletes smoothly.
  - Key numbers count up on first view.
  - Screen transitions: short fade + small slide, 150 to 250 ms.
  - Emergency card flips to show the lock-screen preview.
- ALWAYS respect Reduce Motion (use Reanimated's useReducedMotion): disable or simplify animation when on.
- No looping decorative animation. Nothing that delays the user.

## Layout
- Generous whitespace, clear hierarchy, one primary action per screen.
- Touch targets at least 44x44 points. Add accessibilityLabel to every button and icon.
- Emergency screen: maximum clarity, huge Call 911 button, zero decoration.