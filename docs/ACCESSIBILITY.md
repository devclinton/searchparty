# Accessibility (WCAG 2.1 AA)

## Audit Checklist

### Perceivable
- [ ] All images have alt text
- [ ] Color is not the only means of conveying information (POD heatmap has text labels)
- [ ] Sufficient color contrast (4.5:1 for normal text, 3:1 for large text)
- [ ] Text can be resized to 200% without loss of content
- [ ] Audio/video content has captions (N/A currently)

### Operable
- [ ] All functionality available via keyboard
- [ ] No keyboard traps
- [ ] Focus order is logical and intuitive
- [ ] Focus indicators are visible
- [ ] Skip navigation link present
- [ ] Page titles are descriptive
- [ ] Link purposes are clear from context

### Understandable
- [ ] Language is declared in HTML (`lang` attribute — implemented via next-intl)
- [ ] Form inputs have associated labels
- [ ] Error messages identify the field and describe the error
- [ ] Consistent navigation across pages

### Robust
- [ ] Valid HTML markup
- [ ] ARIA roles and properties used correctly
- [ ] Compatible with screen readers (VoiceOver, NVDA, JAWS)

## Map Accessibility
Maps present unique accessibility challenges:
- Provide text alternatives for all map data (coordinate lists, hazard descriptions)
- Keyboard navigation for map markers and controls
- Screen reader announcements for geofence alerts and status changes
- High-contrast mode for map overlays

## Implementation Notes
- Use semantic HTML elements (`<nav>`, `<main>`, `<article>`, etc.)
- Use `aria-live` regions for dynamic status updates (sync status, GPS tracking)
- Ensure all interactive elements have focus styles
- Test with axe-core browser extension and Lighthouse accessibility audit
