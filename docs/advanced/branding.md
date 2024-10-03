# Advanced

## Branding

InsightBoard is a web application that is designed to be white-labeled. This means that the application can be customized to match the branding of the organization that is using it. This document describes how to customize the branding of InsightBoard.

InsightBoard uses the Bootstrap framework for styling. The Bootstrap framework is a popular CSS framework that provides a set of styles that can be used to create a consistent look and feel across an application. InsightBoard uses the Bootswatch theme for Bootstrap to provide a more visually appealing look and feel.

To customize the branding of InsightBoard, you can override the variables that are used in the Bootswatch theme. The variables that can be overridden include the primary color, secondary color, and other colors that are used in the theme. You can also override the fonts that are used in the theme.

While you can customize the theme to a great extent, a simple way to customize the theme is to use an existing template and adjust the primary and secondary colors to match your branding. This can be done by importing the Bootswatch theme and then overriding the variables that are used in the theme.

### Customizing the Branding

To create a custom `.css`, make sure you have `npm` installed, then navigate to a folder (e.g. `InsightBoard/style`) and install `bootswatch` with `npm install bootswatch`. Next, create a Sassy CSS (`.scss`) file and import the Bootswatch theme and override the variables that are used in that theme.

For example, to override the primary and secondary colors of the Minty theme to a gold and green style, you can create a `custom.scss` file with the following content:

```scss
// Override the primary and secondary colors
$primary: #E1C158;
$secondary: #7DAA6A;

// Import Bootstrap after overriding variables
@import "node_modules/bootswatch/dist/minty/variables";
@import "node_modules/bootstrap/scss/bootstrap";
@import "node_modules/bootswatch/dist/minty/bootswatch";
```

Next, compile the `.scss` file to a `.css` file with `sass custom.scss custom.css`. Finally, move the `.css` file to the `InsightBoard/style`. This folder will be picked-up by `InsightBoard` on startup and the custom theme will be applied.

The bootswatch theme will use the primary and secondary colours to produce a theme that is consistent with the branding, though note that it may be worth selecting a base theme (minty in this case) that is close to the desired branding to minimize the amount of customisation required.

You can make further customizations to the theme by overriding other variables that are used in the Bootswatch theme, or create a new theme. For a list of variables that can be overridden, refer to the Bootswatch documentation.

### Logo

To add a logo to the application, you can place a `logo.png` file in the `InsightBoard/style` folder. The logo will be displayed in the upper-left corner of the application.

The logo has the class-name `logo`, allowing to add further styling to the custom `.css` file if you wish. For example, to add a border to the logo in the secondary color, you can add the following CSS to the `custom.css` file:

```css
.logo {
    border: 1px solid var(--bs-secondary);
}
```
