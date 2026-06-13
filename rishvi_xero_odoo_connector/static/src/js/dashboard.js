/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Widget } from "@web/views/widgets/widget";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { odoo } from "@odoo/owl";

	export class XeroDashboardViewNew extends Component {
	static template = "XeroDashboardViewNew";
	setup() {
        // this.rpc = useService("rpc");
        this.rpc = rpc;
        this.action = useService("action");

        console.log("2222222222222222222222222222222222222222222222222222222")
        self = this
//		PURCHASE
this.rpc("/web/dataset/call_kw/purchase.order/get_pending_order_counts", {
                model: "purchase.order",
                method: "get_pending_order_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#pending_order').text(res)
                var total_order = res

self.rpc("/web/dataset/call_kw/purchase.order/get_waiting_bill_counts", {
                model: "purchase.order",
                method: "get_waiting_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#completed_bill').text(res)
                var waiting_bill = res


                self.rpc("/web/dataset/call_kw/account.move/get_unpaid_bill_counts", {
                model: "account.move",
                method: "get_unpaid_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#unpaid_order').text(res)
                var unpaid_order = res

                self.rpc("/web/dataset/call_kw/account.move/get_paid_bill_counts", {
                model: "account.move",
                method: "get_paid_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#paid_order').text(res)
                var paid_order = res

                self.rpc("/web/dataset/call_kw/purchase.order/purchase_piechart_detail", {
                model: "purchase.order",
                method: "purchase_piechart_detail",
                args: [total_order,paid_order,unpaid_order,waiting_bill],
                kwargs: {},
            }).then(function(res) {
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);

            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);

            var options = {
              is3D:true
            };

            var chart = new google.visualization.PieChart(document.getElementById('chartContainer'));
              chart.draw(data, options);
            }
            });
            });
            });
            });
            });


//		SALE
            self.rpc("/web/dataset/call_kw/sale.order/get_pending_sale_order_counts", {
                model: "sale.order",
                method: "get_pending_sale_order_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#pending_sale_order').text(res)
                var sale_order = res



self.rpc("/web/dataset/call_kw/sale.order/get_waiting_invoice_counts", {
                model: "sale.order",
                method: "get_waiting_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#completed_invoice').text(res)
                var waiting_sale = res

                self.rpc("/web/dataset/call_kw/account.move/get_unpaid_invoice_counts", {
                model: "account.move",
                method: "get_unpaid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#unpaid_sale_order').text(res)
                var unpaid_sale = res

                    self.rpc("/web/dataset/call_kw/account.move/get_paid_invoice_counts", {
                model: "account.move",
                method: "get_paid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#paid_sale_order').text(res)
                var paid_sale = res



                self.rpc("/web/dataset/call_kw/sale.order/sale_piechart_detail", {
                model: "sale.order",
                method: "sale_piechart_detail",
                args: [paid_sale,unpaid_sale,waiting_sale,sale_order],
                kwargs: {},
            }).then(function(res) {
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);

            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);

            var options = {
              is3D:true
            };

            var chart = new google.visualization.PieChart(document.getElementById('chartContainer1'));
              chart.draw(data, options);
            }
            });
            });
            });
            });
            });



//		INVOICE
            self.rpc("/web/dataset/call_kw/account.move/get_pending_invoice_counts", {
                model: "account.move",
                method: "get_pending_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#pending_invoice').text(res)
                var total_invoice= res

                        self.rpc("/web/dataset/call_kw/account.move/get_xero_unpaid_invoice_counts", {
                model: "account.move",
                method: "get_xero_unpaid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#unpaid_invoice').text(res)
                var unpaid_invoice=res

                self.rpc("/web/dataset/call_kw/account.move/get_xero_paid_invoice_counts", {
                model: "account.move",
                method: "get_xero_paid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#paid_invoice').text(res)
                var paid_invoice = res

                self.rpc("/web/dataset/call_kw/account.move/invoice_piechart_detail", {
                model: "account.move",
                method: "invoice_piechart_detail",
                args: [paid_invoice,unpaid_invoice,total_invoice],
                kwargs: {},
            }).then(function(res) {
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);

            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);

            var options = {
              is3D:true
            };

            var chart = new google.visualization.PieChart(document.getElementById('chartContainer2'));
              chart.draw(data, options);
            }
            });
            });
            });
            });


//		BILL


             self.rpc("/web/dataset/call_kw/account.move/get_pending_bill_counts", {
                model: "account.move",
                method: "get_pending_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#pending_bill').text(res)
                var bill_total = res

                           self.rpc("/web/dataset/call_kw/account.move/get_unpaid_xero_bill_counts", {
                model: "account.move",
                method: "get_unpaid_xero_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#unpaid_bill').text(res)
                var unpaid = res

                    self.rpc("/web/dataset/call_kw/account.move/get_paid_xero_bill_counts", {
                model: "account.move",
                method: "get_paid_xero_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#paid_bill').text(res)
                var paid =res


self.rpc("/web/dataset/call_kw/account.move/bill_piechart_detail", {
                model: "account.move",
                method: "bill_piechart_detail",
                args: [paid,unpaid,bill_total],
                kwargs: {},
            }).then(function(res) {
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);

            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);

            var options = {
              is3D:true
            };

            var chart = new google.visualization.PieChart(document.getElementById('chartContainer3'));
              chart.draw(data, options);
            }
            });
            });
            });
            });





//		PURCHASE

		       $('.as_today_meeting_table .today_meeting_line').remove();
		       self.rpc("/web/dataset/call_kw/purchase.order/get_purchase_order_details", {
                model: "purchase.order",
                method: "get_purchase_order_details",
                args: ['last_month'],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {

                    var tr = '';
                   $('.as_today_meeting_table tbody').append('<tr class="today_meeting_line"><td class="o_report_line_header29"><span>'+ rec.quotation_number[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.create_date[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.total[j] +'</span></td></tr>')
                   }
               }
		});

//		SALE


		       $('.as_today_meeting_table1 .today_meeting_line').remove();

		       self.rpc("/web/dataset/call_kw/sale.order/get_sale_order_details", {
                model: "sale.order",
                method: "get_sale_order_details",
                args: ['last_month'],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {

                    var tr = '';
                   $('.as_today_meeting_table1 tbody').append('<tr class="today_meeting_line"><td class="o_report_line_header29"><span>'+ rec.quotation_number[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.create_date[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.total[j] +'</span></td></tr>')
                   }
               }
		});


//		INVOICE
                    self.rpc("/web/dataset/call_kw/account.move/get_pending_invoice_counts", {
                model: "account.move",
                method: "get_pending_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#pending_invoice').text(res)

		});

		self.rpc("/web/dataset/call_kw/sale.order/get_waiting_invoice_counts", {
                model: "sale.order",
                method: "get_waiting_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#completed_invoice').text(res)

		});

		self.rpc("/web/dataset/call_kw/account.move/get_xero_unpaid_invoice_counts", {
                model: "account.move",
                method: "get_xero_unpaid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#unpaid_invoice').text(res)

		});

		self.rpc("/web/dataset/call_kw/account.move/get_xero_paid_invoice_counts", {
                model: "account.move",
                method: "get_xero_paid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#paid_invoice').text(res)

		});
		       $('.as_today_meeting_table2 .today_meeting_line').remove();

		       self.rpc("/web/dataset/call_kw/account.move/get_invoice_details", {
                model: "account.move",
                method: "get_invoice_details",
                args: ['last_month'],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {

                    var tr = '';
                   $('.as_today_meeting_table2 tbody').append('<tr class="today_meeting_line"><td class="o_report_line_header29"><span>'+ rec.quotation_number[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.create_date[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.total[j] +'</span></td></tr>')
                   }
               }
		});


//		Bill

                self.rpc("/web/dataset/call_kw/account.move/get_pending_bill_counts", {
                model: "account.move",
                method: "get_pending_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#pending_bill').text(res)

		});

		self.rpc("/web/dataset/call_kw/purchase.order/get_waiting_bill_counts", {
                model: "purchase.order",
                method: "get_waiting_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#completed_bill').text(res)

		});

		self.rpc("/web/dataset/call_kw/account.move/get_unpaid_xero_bill_counts", {
                model: "account.move",
                method: "get_unpaid_xero_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#unpaid_bill').text(res)

		});
		self.rpc("/web/dataset/call_kw/account.move/get_paid_xero_bill_counts", {
                model: "account.move",
                method: "get_paid_xero_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                $('#paid_bill').text(res)

		});
		       $('.as_today_meeting_table3 .today_meeting_line').remove();

		       self.rpc("/web/dataset/call_kw/account.move/get_bill_details", {
                model: "account.move",
                method: "get_bill_details",
                args: ['last_month'],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {

                    var tr = '';
                   $('.as_today_meeting_table3 tbody').append('<tr class="today_meeting_line"><td class="o_report_line_header29"><span>'+ rec.quotation_number[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.create_date[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.total[j] +'</span></td></tr>')
                   }
               }
		});


        }


        init() {
        this.actionManager = parent;
        return this._super.apply(this, arguments);
        }

        open_co_living_record(e) {
        $('.o_stock_reports_table').show();
        }





//        DYNAMIC CHART

        async on_DataType() {
        self = this
        var element = document. getElementById('TimeData').value;

        this.rpc("/web/dataset/call_kw/purchase.order/get_waiting_bill_counts", {
                model: "purchase.order",
                method: "get_waiting_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#completed_bill').text(res)
                var waiting_bill=res
                console.log

        self.rpc("/web/dataset/call_kw/account.move/get_unpaid_bill_counts", {
                model: "account.move",
                method: "get_unpaid_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#unpaid_order').text(res)
                var unpaid_order=res

           self.rpc("/web/dataset/call_kw/account.move/get_paid_bill_counts", {
                model: "account.move",
                method: "get_paid_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#paid_order').text(res)
                var paid_order=res

                self.rpc("/web/dataset/call_kw/purchase.order/get_pending_order_counts", {
                model: "purchase.order",
                method: "get_pending_order_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#pending_order').text(res)
                var total_order=res


                self.rpc("/web/dataset/call_kw/purchase.order/purchase_piechart_detail", {
                model: "purchase.order",
                method: "purchase_piechart_detail",
                args: [total_order,paid_order,unpaid_order,waiting_bill],
                kwargs: {},
            }).then(function(res) {
			           var charttype=document.getElementById("DataType").value;
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);

            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);

   if (charttype == 'pie') {
                var options = {
                    is3D:true
                         };

                    var chart = new google.visualization.PieChart(document.getElementById('chartContainer'));
                    chart.draw(data, options);
                } else if (charttype == 'bar') {
                  var options = {
                };
                    var chart = new google.visualization.BarChart(document.getElementById('chartContainer'));
                      chart.draw(data, options);
                    } else {
                      var options = {
                      legend: 'none'
                    };
                    // Draw
                    var chart = new google.visualization.ScatterChart(document.getElementById('chartContainer'));
                    chart.draw(data, options);
                }

            }


//            PURCHASE TABLE ON CLICK
        var element = document. getElementById('TimeData').value;
        $('.as_today_meeting_table .today_meeting_line').remove();


        self.rpc("/web/dataset/call_kw/purchase.order/get_purchase_order_details", {
                model: "purchase.order",
                method: "get_purchase_order_details",
                args: [element],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {

                    var tr = '';
                   $('.as_today_meeting_table tbody').append('<tr class="today_meeting_line"><td class="o_report_line_header29"><span>'+ rec.quotation_number[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.create_date[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.total[j] +'</span></td></tr>')
                   }
               }
		});
			});
		});
		});
		});
		   });
        }

        async on_DataType1() {
        self = this
                       var element = document. getElementById('TimeData1').value;
                       self.rpc("/web/dataset/call_kw/sale.order/get_pending_sale_order_counts", {
                model: "sale.order",
                method: "get_pending_sale_order_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#pending_sale_order').text(res)
                var sale_order = res

                self.rpc("/web/dataset/call_kw/sale.order/get_waiting_invoice_counts", {
                model: "sale.order",
                method: "get_waiting_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#completed_invoice').text(res)
                var waiting_sale = res

                self.rpc("/web/dataset/call_kw/account.move/get_unpaid_invoice_counts", {
                model: "account.move",
                method: "get_unpaid_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#unpaid_sale_order').text(res)
                var unpaid_sale = res

                self.rpc("/web/dataset/call_kw/account.move/get_paid_invoice_counts", {
                model: "account.move",
                method: "get_paid_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#paid_sale_order').text(res)
                var paid_sale = res
                self.rpc("/web/dataset/call_kw/sale.order/sale_piechart_detail", {
                model: "sale.order",
                method: "sale_piechart_detail",
                args: [paid_sale,unpaid_sale,waiting_sale,sale_order],
                kwargs: {},
            }).then(function(res) {

			           var charttype=document.getElementById("DataType1").value;

			           google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);

            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);

   if (charttype == 'pie') {
                var options = {
                    is3D:true
                         };

                    var chart = new google.visualization.PieChart(document.getElementById('chartContainer1'));
                    chart.draw(data, options);
                } else if (charttype == 'bar') {
                  var options = {
                };
                    var chart = new google.visualization.BarChart(document.getElementById('chartContainer1'));
                      chart.draw(data, options);
                    } else {
                      var options = {
                      legend: 'none'
                    };
                    // Draw
                    var chart = new google.visualization.ScatterChart(document.getElementById('chartContainer1'));
                    chart.draw(data, options);
                }

            }



		});
				});
		});
		});
		});
	    $('.as_today_meeting_table1 .today_meeting_line').remove();

	    self.rpc("/web/dataset/call_kw/sale.order/get_sale_order_details", {
                model: "sale.order",
                method: "get_sale_order_details",
                args: [element],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {

                    var tr = '';
                   $('.as_today_meeting_table1 tbody').append('<tr class="today_meeting_line"><td class="o_report_line_header29"><span>'+ rec.quotation_number[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.create_date[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.total[j] +'</span></td></tr>')
                   }
               }
		});

        }


        async on_DataType2() {
        self = this
                var element = document. getElementById('TimeData2').value;
                self.rpc("/web/dataset/call_kw/account.move/get_pending_invoice_counts", {
                model: "account.move",
                method: "get_pending_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#pending_invoice').text(res)
                var total_invoice= res
                self.rpc("/web/dataset/call_kw/account.move/get_xero_unpaid_invoice_counts", {
                model: "account.move",
                method: "get_xero_unpaid_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#unpaid_invoice').text(res)
                var unpaid_invoice=res
                self.rpc("/web/dataset/call_kw/account.move/get_xero_paid_invoice_counts", {
                model: "account.move",
                method: "get_xero_paid_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#paid_invoice').text(res)
                var paid_invoice = res

                self.rpc("/web/dataset/call_kw/account.move/invoice_piechart_detail", {
                model: "account.move",
                method: "invoice_piechart_detail",
                args: [paid_invoice,unpaid_invoice,total_invoice],
                kwargs: {},
            }).then(function(res) {

			           var charttype=document.getElementById("DataType2").value;
			           google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);

            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);

   if (charttype == 'pie') {
                var options = {
                    is3D:true
                         };

                    var chart = new google.visualization.PieChart(document.getElementById('chartContainer2'));
                    chart.draw(data, options);
                } else if (charttype == 'bar') {
                  var options = {
                };
                    var chart = new google.visualization.BarChart(document.getElementById('chartContainer2'));
                      chart.draw(data, options);
                    } else {
                      var options = {
                      legend: 'none'
                    };
                    // Draw
                    var chart = new google.visualization.ScatterChart(document.getElementById('chartContainer2'));
                    chart.draw(data, options);
                }

            }

		});
			});
		});
		});
		$('.as_today_meeting_table2 .today_meeting_line').remove();
		self.rpc("/web/dataset/call_kw/account.move/get_invoice_details", {
                model: "account.move",
                method: "get_invoice_details",
                args: [element],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {

                    var tr = '';
                   $('.as_today_meeting_table2 tbody').append('<tr class="today_meeting_line"><td class="o_report_line_header29"><span>'+ rec.quotation_number[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.create_date[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.total[j] +'</span></td></tr>')
                   }
               }
		});



        }

        async on_DataType3() {
                       self = this
                        var element = document. getElementById('TimeData3').value;

             self.rpc("/web/dataset/call_kw/account.move/get_pending_bill_counts", {
                model: "account.move",
                method: "get_pending_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#pending_bill').text(res)
                var bill_total = res

                self.rpc("/web/dataset/call_kw/account.move/get_unpaid_xero_bill_counts", {
                model: "account.move",
                method: "get_unpaid_xero_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#unpaid_bill').text(res)
                var unpaid = res


                self.rpc("/web/dataset/call_kw/account.move/get_paid_xero_bill_counts", {
                model: "account.move",
                method: "get_paid_xero_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                $('#paid_bill').text(res)
                var paid =res

                self.rpc("/web/dataset/call_kw/account.move/bill_piechart_detail", {
                model: "account.move",
                method: "bill_piechart_detail",
                args: [paid,unpaid,bill_total],
                kwargs: {},
            }).then(function(res) {

			           var charttype=document.getElementById("DataType3").value;

			           			           google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);

            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);

   if (charttype == 'pie') {
                var options = {
                    is3D:true
                         };

                    var chart = new google.visualization.PieChart(document.getElementById('chartContainer3'));
                    chart.draw(data, options);
                } else if (charttype == 'bar') {
                  var options = {
                };
                    var chart = new google.visualization.BarChart(document.getElementById('chartContainer3'));
                      chart.draw(data, options);
                    } else {
                      var options = {
                      legend: 'none'
                    };
                    // Draw
                    var chart = new google.visualization.ScatterChart(document.getElementById('chartContainer3'));
                    chart.draw(data, options);
                }

            }

		});

		});
		});
		});

	    $('.as_today_meeting_table3 .today_meeting_line').remove();
	    self.rpc("/web/dataset/call_kw/account.move/get_paid_xero_bill_counts", {
                model: "account.move",
                method: "get_bill_details",
                args: [element],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {

                    var tr = '';
                   $('.as_today_meeting_table3 tbody').append('<tr class="today_meeting_line"><td class="o_report_line_header29"><span>'+ rec.quotation_number[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.create_date[j] +'</span></td><td class="o_report_line_header29"><span>'+ rec.total[j] +'</span></td></tr>')
                   }
               }
		});



        }


//ON CLICK PURCHASE ORDER

        async on_pending_order(){
        self = this
        var element = document. getElementById('TimeData').value;
          let context = this;
          self.rpc("/web/dataset/call_kw/purchase.order/fetch_purchase_id", {
                model: "purchase.order",
                method: "fetch_purchase_id",
                args: [element],
                kwargs: {},
            }).then(function(res) {

        self.action.doAction({
                name: _t('Purchase Order'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'purchase.order',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            });

        }


        async on_completed_order() {
        self = this
        self.action.doAction({
                name: _t('Purchase Order'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'purchase.order',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : ['&',["state", "=", "done"],["xero_purchase_id", "!=", false]],
            });

        }

        async on_paid_order() {
        var element = document. getElementById('TimeData').value;
        self = this
          let context = this;
        				self.rpc("/web/dataset/call_kw/account.move/get_paid_bill_id", {model:'account.move',
			           method:'get_paid_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
			           console.log("222222222222222222222222222222222222222222222",res)
        self.action.doAction({
                name: _t('Bill'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in",res]],
            });
            	});

        }

        async on_unpaid_order() {
        var element = document. getElementById('TimeData').value;
        self = this
          let context = this;
          				self.rpc("/web/dataset/call_kw/account.move/get_unpaid_bill_id", {model:'account.move',
			           method:'get_unpaid_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Bill'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            });

        }



//        ON CLICK SALE ORDER


        async on_completed_invoice() {
        var element = document. getElementById('TimeData1').value;
        self = this
        let context = this;
        self.rpc("/web/dataset/call_kw/sale.order/get_waiting_invoice_id", {model:'sale.order',
			           method:'get_waiting_invoice_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
			           localStorage.res = res;
			           self.action.doAction({
                            name: _t('Invoice'),
                            views: [[false, 'list'], [false, 'form']],
                            view_type: 'form',
                            view_mode: 'list,form',
                            res_model: 'sale.order',
                            type: 'ir.actions.act_window',
                            target: 'current',
                            domain : [["id", "=", res]],
                        });
			            });
        }






        async on_pending_sale_order() {
        var element = document. getElementById('TimeData1').value;
        self = this
        let context = this;
                self.rpc("/web/dataset/call_kw/sale.order/get_pending_sale_order_id", {model:'sale.order',
			           method:'get_pending_sale_order_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                 name: _t('Sale Order'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'sale.order',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            		});

        }

        async on_completed_sale_order() {
        self = this
        self.action.doAction({
                name: _t('Sale Order'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'sale.order',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : ['&',["state", "=", "done"],["xero_sale_id", "!=", false]],
            });

        }

        async on_paid_sale_order() {
        var element = document. getElementById('TimeData1').value;
        self = this
          let context = this;
        					self.rpc("/web/dataset/call_kw/account.move/get_paid_invoice_id", {model:'account.move',
			           method:'get_paid_invoice_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
			           console.log("resresresresresresresresresresres",res)
        self.action.doAction({
                name: _t('Invoice'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "=", res]],
            });
            		});

        }

        async on_unpaid_sale_order() {
        var element = document. getElementById('TimeData1').value;
        self = this
          let context = this;
          			    self.rpc("/web/dataset/call_kw/account.move/get_unpaid_invoice_id", {model:'account.move',
			           method:'get_unpaid_invoice_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Invoice'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            		});

        }



//        Invoice

        async on_pending_invoice() {
        var element = document. getElementById('TimeData2').value;
        self = this
          let context = this;
                      self.rpc("/web/dataset/call_kw/account.move/get_pending_invoice_id", {model:'account.move',
			           method:'get_pending_invoice_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Invoices'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            	});

        }


        async on_paid_invoice() {
        var element = document. getElementById('TimeData2').value;
        self = this
          let context = this;
        				self.rpc("/web/dataset/call_kw/account.move/get_xero_paid_invoice_id", {model:'account.move',
			           method:'get_xero_paid_invoice_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Invoice'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "=",res]],
            });
            });

        }

        async on_unpaid_invoice() {
        var element = document. getElementById('TimeData2').value;
        self = this
          let context = this;
            		   self.rpc("/web/dataset/call_kw/account.move/get_xero_unpaid_invoice_cid", {model:'account.move',
			           method:'get_xero_unpaid_invoice_cid',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Invoice'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in",res]],
            });
            });

        }


//        BILL


        async on_pending_bill() {
        var element = document. getElementById('TimeData3').value;
        self = this
          let context = this;
                    self.rpc("/web/dataset/call_kw/account.move/get_pending_bill_id", {model:'account.move',
			           method:'get_pending_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Bill'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            });

        }

        async on_completed_bill() {
        var element = document. getElementById('TimeData').value;
        self = this
        let context = this;
        self.rpc("/web/dataset/call_kw/purchase.order/get_waiting_bill_id", {model:'purchase.order',
			           method:'get_waiting_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
			           localStorage.res = res;
			           self.action.doAction({
                            name: _t('Bill'),
                            views: [[false, 'list'], [false, 'form']],
                            view_type: 'form',
                            view_mode: 'list,form',
                            res_model: 'purchase.order',
                            type: 'ir.actions.act_window',
                            target: 'current',
                            domain : [["id", "=", res]],
                        });
			            });
        }

        async on_paid_bill() {
        var element = document. getElementById('TimeData3').value;
        self = this
          let context = this;
        				self.rpc("/web/dataset/call_kw/account.move/get_paid_xero_bill_id", {model:'account.move',
			           method:'get_paid_xero_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Bill'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            });

        }

        async on_unpaid_bill() {
        var element = document. getElementById('TimeData3').value;
        self= this

          let context = this;
        				self.rpc("/web/dataset/call_kw/account.move/get_unpaid_xero_bill_id", {model:'account.move',
			           method:'get_unpaid_xero_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Bill'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            	});
        }
		}
registry.category("actions").add("meeting_chart", XeroDashboardViewNew);