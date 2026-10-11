Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$outputPath = Join-Path (Get-Location) "speaker_reference.wav"
$synth.SetOutputToWaveFile($outputPath)
$synth.Speak("Hello, this is a clear speaker reference audio.")
$synth.Dispose()
Write-Output "Generated speaker_reference.wav successfully!"
