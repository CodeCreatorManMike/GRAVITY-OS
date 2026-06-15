import { Tabs } from 'expo-router';
import { Text } from 'react-native';

const INK = '#14130d';
const PAPER = '#f4f2ea';

function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  return (
    <Text style={{ fontSize: 10, color: focused ? INK : '#888', letterSpacing: 1, fontWeight: focused ? '700' : '400' }}>
      {label}
    </Text>
  );
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarStyle: {
          backgroundColor: PAPER,
          borderTopColor: 'rgba(20,19,13,0.1)',
          height: 56,
          paddingBottom: 8,
        },
        tabBarActiveTintColor: INK,
        tabBarInactiveTintColor: '#888',
        headerShown: false,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'HOME',
          tabBarIcon: ({ focused }) => <TabIcon label="◉" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="health"
        options={{
          title: 'HEALTH',
          tabBarIcon: ({ focused }) => <TabIcon label="♡" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: 'SETTINGS',
          tabBarIcon: ({ focused }) => <TabIcon label="⊞" focused={focused} />,
        }}
      />
    </Tabs>
  );
}
