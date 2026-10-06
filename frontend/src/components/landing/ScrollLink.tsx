"use client";

import { AnchorHTMLAttributes } from "react";
import { useSmoothScroll } from "@/hooks/useSmoothScroll";

interface ScrollLinkProps
    extends AnchorHTMLAttributes<HTMLAnchorElement> {
    href: string;
}

export default function ScrollLink({
    href,
    children,
    onClick,
    className,
    ...rest
}: ScrollLinkProps) {
    const smoothScroll = useSmoothScroll();

    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
        onClick?.(e);
        smoothScroll(e, href);
    };

    return (
        <a href={href} className={className} onClick={handleClick} {...rest}>
            {children}
        </a>
    );
}
