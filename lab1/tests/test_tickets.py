import pytest

from ticket_generator.tickets import TicketGenerator


def test_ticket_is_within_range():
    generator = TicketGenerator(1, 20)
    tickets = {generator.next_ticket() for _ in range(1000)}

    assert tickets <= set(range(1, 21))
    assert len(tickets) == 20


def test_empty_range_is_rejected():
    with pytest.raises(ValueError):
        TicketGenerator(5, 1)
