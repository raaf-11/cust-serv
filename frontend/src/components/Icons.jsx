// Small stroke icons used across pages (no icon library needed).

function Svg({ children, ...props }) {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            {...props}
        >
            {children}
        </svg>
    );
}

export const PlusIcon = () => (
    <Svg><path d="M12 5v14M5 12h14" /></Svg>
);

export const SendIcon = () => (
    <Svg><path d="M12 19V5M6 11l6-6 6 6" /></Svg>
);

export const TrashIcon = () => (
    <Svg><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" /></Svg>
);

export const MenuIcon = () => (
    <Svg><path d="M4 7h16M4 12h16M4 17h16" /></Svg>
);

export const CloseIcon = () => (
    <Svg><path d="M6 6l12 12M18 6L6 18" /></Svg>
);

export const BackIcon = () => (
    <Svg><path d="M15 18l-6-6 6-6" /></Svg>
);

export const SignOutIcon = () => (
    <Svg><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l-5-5 5-5M5 12h11" /></Svg>
);

export const CheckIcon = () => (
    <Svg><path d="M5 12.5l4.5 4.5L19 7.5" /></Svg>
);
