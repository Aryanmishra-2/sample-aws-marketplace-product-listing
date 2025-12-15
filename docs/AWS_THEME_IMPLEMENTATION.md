# AWS Marketplace Theme Implementation

## Date: December 2, 2025

## Overview
Applied AWS Marketplace branding and theme colors throughout the application to match the official AWS design language.

## AWS Color Palette

### Primary Colors
- **Squid Ink** (#232f3e) - Primary dark background
- **Smile Orange** (#ff9900) - Primary accent color
- **Pacific Blue** (#0073bb) - Secondary accent
- **Deep Squid Ink** (#16191f) - Text primary

### Status Colors
- **Success Green** (#037f0c) - Success states
- **Warning Yellow** (#f89406) - Warning states
- **Error Red** (#d13212) - Error states
- **Info Blue** (#0073bb) - Information states

### Neutral Colors
- **Light Gray** (#eaeded) - Backgrounds
- **Medium Gray** (#aab7b8) - Secondary text
- **Dark Gray** (#545b64) - Tertiary text

## Components Updated

### 1. Global Header
**Branding:**
- AWS Marketplace logo with orange accent
- "Seller Portal" subtitle
- 4px orange bottom border for emphasis
- Box shadow for depth

**Account Information:**
- AWS Account ID display
- IAM User name
- Organization badge (color-coded by region)
- Product ID (when applicable)

**Navigation:**
- Home button with orange hover effect
- Clear Data button with red theme
- Smooth hover transitions

**Progress Bar:**
- Orange gradient for in-progress
- Green gradient for completion
- Animated shimmer effect
- Glowing shadow effect
- Step counter and percentage

### 2. Global Styles (globals.css)
**CSS Variables:**
```css
--aws-squid-ink: #232f3e;
--aws-smile-orange: #ff9900;
--aws-pacific-blue: #0073bb;
--aws-success-green: #037f0c;
--aws-error-red: #d13212;
```

**Utility Classes:**
- `.aws-progress-step` - Step indicators
- `.aws-badge` - Status badges
- `.aws-card` - Card containers
- `.aws-button-primary` - Primary buttons
- `.aws-button-secondary` - Secondary buttons

**Animations:**
- `pulse` - Pulsing effect for in-progress items
- `shimmer` - Shimmer effect for progress bars

### 3. CloudScape Components
Using AWS's official CloudScape Design System which includes:
- AppLayout
- Container
- Header
- Button
- Badge
- StatusIndicator
- Table
- Alert

All components automatically use AWS theme colors.

## Design Principles

### 1. Consistency
- All colors match AWS Marketplace official palette
- Consistent spacing and typography
- Uniform component styling

### 2. Accessibility
- High contrast ratios for text
- Clear visual hierarchy
- Keyboard navigation support
- Screen reader friendly

### 3. Responsiveness
- Mobile-friendly layouts
- Flexible grid systems
- Adaptive component sizing

### 4. Performance
- CSS-only animations
- Minimal JavaScript for styling
- Optimized asset loading

## Visual Hierarchy

### Primary Actions
- Orange (#ff9900) buttons
- Bold, prominent placement
- Clear call-to-action text

### Secondary Actions
- White/transparent buttons with borders
- Less prominent but accessible
- Hover effects for feedback

### Status Indicators
- Color-coded badges
- Icon + text combinations
- Consistent positioning

### Information Display
- Dark backgrounds for headers
- Light backgrounds for content
- Clear section separation

## Branding Elements

### Logo Treatment
- "AWS Marketplace" in orange
- Vertical separator
- "Seller Portal" in gray
- Consistent placement in header

### Progress Indication
- Orange gradient bar
- Animated shimmer effect
- Step counter
- Percentage display

### Account Information
- Structured data display
- Color-coded organization badges
- Truncated IDs for readability

## Hover Effects

### Buttons
```css
/* Home Button */
transparent → orange background
white text → dark text

/* Clear Data Button */
transparent → red background
red text → white text
```

### Cards
```css
border: default → hover color
shadow: none → subtle shadow
```

## Animation Details

### Progress Bar Shimmer
- 2-second loop
- Smooth gradient movement
- Only active during progress
- Stops at 100%

### Pulse Effect
- 2-second loop
- Opacity: 1 → 0.7 → 1
- Applied to in-progress items

## Typography

### Font Family
```css
font-family: "Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif;
```

### Font Sizes
- **Heading 1**: 20px, bold
- **Heading 2**: 16px, bold
- **Body**: 14px, regular
- **Small**: 12px, regular

### Font Weights
- **Bold**: 700 (headings, emphasis)
- **Semi-bold**: 600 (buttons, labels)
- **Regular**: 400 (body text)

## Spacing System

### Padding
- **Small**: 8px
- **Medium**: 12px
- **Large**: 16px
- **XLarge**: 20px

### Margins
- **XSmall**: 4px
- **Small**: 8px
- **Medium**: 12px
- **Large**: 16px

### Gaps
- **XSmall**: 4px
- **Small**: 8px
- **Medium**: 12px
- **Large**: 16px

## Border Radius

- **Small**: 4px (buttons, badges)
- **Medium**: 8px (cards, containers)

## Shadows

### Elevation Levels
- **Level 1**: `0 2px 4px rgba(0, 0, 0, 0.1)` - Subtle
- **Level 2**: `0 2px 8px rgba(0, 0, 0, 0.15)` - Medium
- **Level 3**: `0 4px 12px rgba(0, 0, 0, 0.2)` - Prominent

### Glow Effects
- **Orange Glow**: `0 0 10px rgba(255, 153, 0, 0.6)`
- **Blue Glow**: `0 0 8px rgba(0, 115, 187, 0.5)`

## Future Enhancements

1. **Dark Mode Support**
   - Inverted color scheme
   - Adjusted contrast ratios
   - User preference detection

2. **Custom Themes**
   - Partner branding options
   - White-label capabilities
   - Theme switcher

3. **Enhanced Animations**
   - Page transitions
   - Loading states
   - Success celebrations

4. **Accessibility Improvements**
   - ARIA labels
   - Focus indicators
   - Keyboard shortcuts

## References

- [AWS Design System](https://cloudscape.design/)
- [AWS Brand Guidelines](https://aws.amazon.com/architecture/icons/)
- [CloudScape Components](https://cloudscape.design/components/)
- [AWS Marketplace](https://aws.amazon.com/marketplace/)
