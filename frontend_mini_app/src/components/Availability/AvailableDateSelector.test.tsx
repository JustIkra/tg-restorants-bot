import { fireEvent, render, screen } from "@testing-library/react";

import type { AvailableDay } from "@/components/Availability/AvailableDateSelector";
import AvailableDateSelector from "@/components/Availability/AvailableDateSelector";

const sampleDays: AvailableDay[] = [
  {
    date: "2024-05-20",
    weekday: "понедельник",
    can_order: true,
    deadline: null,
    reason: null,
  },
  {
    date: "2024-05-21",
    weekday: "вторник",
    can_order: false,
    deadline: null,
    reason: "Нет доставки",
  },
  {
    date: "2024-05-22",
    weekday: "среда",
    can_order: true,
    deadline: null,
    reason: null,
  },
];

describe("AvailableDateSelector", () => {
  it("renders available dates and allows selecting enabled day", () => {
    const handleSelect = jest.fn();

    render(
      <AvailableDateSelector
        days={sampleDays}
        selectedDate="2024-05-20"
        onSelect={handleSelect}
        loading={false}
      />
    );

    expect(screen.getByText(/понедельник/i)).toBeInTheDocument();
    expect(screen.getByText("20.05")).toBeInTheDocument();
    expect(screen.getByText(/вторник/i)).toBeInTheDocument();

    const disabledDay = screen.getByRole("button", { name: /21.05/i });
    expect(disabledDay).toBeDisabled();

    const nextDay = screen.getByRole("button", { name: /22.05/i });
    fireEvent.click(nextDay);

    expect(handleSelect).toHaveBeenCalledWith("2024-05-22");
  });
});
