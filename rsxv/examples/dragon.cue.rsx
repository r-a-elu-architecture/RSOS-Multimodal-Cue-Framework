PROTOCOL dragon "steady identity under pressure"
VERSION 1.0
SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4
BREATH inhale=4s exhale=6s

TIER 1 DRAGON {
  V "Deep red light turning to gold"
  A "I hold the storm and breathe"
  K "Slow heat rising along the spine"
}
TIER 2 LION {
  V "A warm golden light"
  A "I lead, calmly"
  K "Steady strength in the chest"
}
FUTURES "Your future self in 3 years" | "A real moment where you will need this"

PHASE gate dur=5s {
  MARK "lin:-|v7:EthicsContain"
  MARK "lin:-|v13:SymbolicDriftCheck"
  FEEL "Check in: are you ready to begin?"
}
REPEAT 15 {
  PHASE settle_in breath=inhale {
    MARK "lin:-|v3:BreathOverride"
    HAPTIC on=300ms off=600ms x=4 amp=0.3
    FEEL "Breathe in slowly, out longer"
    MARK "lin:-|v4:PostureShift"
    GESTURE "Spine tall, shoulders soft"
    MARK "lin:-|v6:EmotionalLock"
    FEEL "Let calm settle in the chest"
  }
  PHASE settle_out breath=exhale {
    FEEL "Breathe out"
  }
}
REPEAT 9 {
  PHASE expand dur=10s {
    MARK "lin:-|v5:MemoryRecall"
    ACTIVATE LION
    MARK "lin:-|v18:AssociativeExpand"
    SEE "Let the image open into everything it connects to"
    MARK "lin:-|v8:CompressionRun"
    SEE "Fold it all into one symbol"
    MARK "lin:-|v10:ArchetypeMerge"
    ACTIVATE LION
    ACTIVATE DRAGON
    SEE "The two become one form"
  }
}
REPEAT 12 {
  PHASE rebuild dur=10s {
    MARK "lin:-|v1:IdentityRebuild"
    SAY "This is who I am becoming"
    MARK "lin:-|v9:FutureProjection"
    FOR FUTURE {
      SEE "$future"
      WAIT 2s
    }
    MARK "lin:-|v11:DeviceOutput"
    SEE "dragon"
  }
}
REPEAT 9 {
  PHASE integrate dur=10s {
    MARK "lin:-|v19:MetaObserve"
    SEE "Watch yourself from a calm distance"
    MARK "lin:-|v21:SelfRevise"
    SAY "I choose what to keep"
    MARK "lin:-|v20:IntegrateAll"
    FEEL "Let every part settle into one"
    MARK "lin:-|v14:RecursiveLawApply"
    SAY "What worked, I keep"
  }
}
REPEAT 2 {
  PHASE close dur=10s {
    MARK "lin:-|v15:MemoryUpdate"
    MARK "lin:-|v17:EchoPropagationStop"
    FEEL "Let it end here"
    MARK "lin:-|v16:SymbolicCommandExport"
  }
}
