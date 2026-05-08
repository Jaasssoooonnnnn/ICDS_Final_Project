# Design References

The GUI refresh follows open-source web app patterns adapted to CustomTkinter
instead of copying code or assets.

## References Used

- `mckaywrigley/chatbot-ui`: clean AI chat workspace with persistent sidebar,
  focused message stream, and concise chat cards.
  https://github.com/mckaywrigley/chatbot-ui
- `Kiranism/next-shadcn-dashboard-starter`: shadcn-style dashboard shell with
  restrained borders, neutral surfaces, compact cards, and clear action panels.
  https://github.com/Kiranism/next-shadcn-dashboard-starter

## Adaptation Notes

- Dark navigation sidebar to separate workspace navigation from content.
- Light central chat canvas with rounded message cards and clear timestamps.
- Right-side action/insight panel with dashboard cards.
- Wider default window and right panel so labels do not truncate during demos.
- Reduced decorative clutter; stronger contrast and spacing hierarchy.
- Game mole spawn points now align with illustrated holes instead of appearing
  in the sky.
