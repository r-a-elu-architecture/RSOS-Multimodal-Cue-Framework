# Swish: the trigger image shrinks and darkens while the resource image grows and brightens; 5 fast repetitions.
PROTOCOL swish "Swish"
VERSION 1.0
REPEAT 5 {
  PHASE swish dur=2s {
    SEE "Trigger image shrinks to a dark dot"
    WAIT 600ms
    SEE "Resource image explodes large and bright"
    HAPTIC on=100ms off=100ms x=3 amp=0.3
  }
  PHASE clear dur=1500ms {
    SEE "Blank screen; open your eyes"
  }
}
