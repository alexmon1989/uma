from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest
from xml.dom import minidom
from xml.parsers.expat import ExpatError
from ..payments.models import Order, OrderOperation
from decimal import Decimal


@require_POST
@csrf_exempt
def pb(request):
    """Принимает запросы от ПБ."""
    try:
        dom = minidom.parseString(request.body)
    except ExpatError:
        return HttpResponseBadRequest('XML parsing error')

    dom.normalize()
    action = dom.getElementsByTagName("Transfer")[0].getAttribute("action")

    if action == 'Search':
        value = dom.getElementsByTagName("Transfer")[0].getElementsByTagName("Unit")[0].getAttribute("value")

        try:
            order = Order.objects.exclude(orderoperation__code=1).get(pk=value)
        except (Order.DoesNotExist, ValueError):
            response = render(None, 'paygate/search_error.xml')
        else:
            data = {
                'billIdentifier': value,
                'order':  order,
            }
            response = render(None, 'paygate/search_success.xml', data)

    elif action == 'Pay':
        bill_identifier = dom.getElementsByTagName("Transfer")[0].getElementsByTagName("Data")[0]\
            .getElementsByTagName("PayerInfo")[0].getAttribute("billIdentifier")

        try:
            order = Order.objects.exclude(orderoperation__code=1).get(pk=bill_identifier)
        except Order.DoesNotExist:
            response = render(None, 'paygate/pay_error.xml')
        else:
            data = dom.getElementsByTagName("Transfer")[0].getElementsByTagName("Data")[0]

            # Лог операций
            OrderOperation.objects.create(
                order=order,
                code=1,
                value=Decimal(data.getElementsByTagName("TotalSum")[0].firstChild.nodeValue),
                pay_request_pb_xml=request.body.decode()
            )

            response = render(None, 'paygate/pay_success.xml', {'reference': data.getAttribute("id")})

    else:
        response = render(None, 'paygate/error_type.xml', {'action': action})

    response['Content-Type'] = 'application/xml;'
    return response
