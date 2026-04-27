#include<stdio.h>
#include<stdlib.h>
struct data
{
  int a;
  struct data *b;
};
void create (int data, struct data **head)
{
  struct data *new, *temp;
  new = (struct data *) malloc (sizeof (struct data));
  new->a = data;
  new->b = 0;
  if (*head == 0)
    {
      *head = temp = new;
    }
  else
    {
      temp->b = new;
      temp = temp->b;
    }
}
 void disp1(struct data *head1)
{
    struct data *temp;
  temp = head1;
  printf ("the elements in the linked list are");
  while (temp != 0)
    {
      printf ("%d ", temp->a);
      temp = temp->b;
    }
}
void createnew (int data, struct data **head1)
{
  struct data *new, *temp;
  new = (struct data *) malloc (sizeof (struct data));
  new->a = data;
  new->b = 0;
  if (*head1 == 0)
    {
      *head1 = temp = new;
    }
  else
    {
      temp->b = new;
      temp = temp->b;
    }
}

void disp (struct data *head)
{
  struct data *temp;
  temp = head;
  printf ("the elements in the linked list are");
  while (temp != 0)
    {
      printf ("%d ", temp->a);
      temp = temp->b;
    }
}

void
addpos1 (int data, struct data *k)
{
  struct data *new, *temp;
  new = (struct data *) malloc (sizeof (struct data));
  new->a = data;
  new->b = k;
  k = new;
  temp = k;
  while (temp != 0)
    {
      printf ("%d ", temp->a);
      temp = temp->b;
    }

}

void count (struct data *x)
{
  int c = 0;
  struct data *temp;

  temp = x;
  while (temp != 0)
    {
      c++;
      temp = temp->b;
    }
    printf("the size of the linked list is %d",c);

  
}

void
removf (struct data *x)
{
  struct data *temp;
  temp = x;
  temp = temp->b;

  printf ("after removing 1st element the linked list is ");
  printf ("\n");
  while (temp != 0)
    {
      printf ("%d ", temp->a);
      temp = temp->b;
    }
  printf ("\n");



}

void ad (struct data *u, int data)
{
  struct data *new_node, *temp, *y,*x;
  x=u;
  new_node = (struct data *) malloc (sizeof (struct data));
  new_node->a = data;
  new_node->b = NULL;
  temp = x;
  while (temp != NULL)
    {
      y = temp;
      temp = temp->b;
    }
     y->b = new_node;
  temp = x;
  while (temp != NULL)
    {
      printf ("%d ", temp->a);
      temp = temp->b;
    }
  printf ("\n");
 
  
  

}

void
re (struct data *d)
{
  struct data *temp, *y;
  temp = d;
  while (temp->b)
    {
      y = temp;
      temp = temp->b;
    }
  y->b = 0;
  temp = d;
  printf("the linked list after deleting the end element is");
  while (temp != 0)
    {
      printf ("%d ", temp->a);
      temp = temp->b;
    }
}

void po (struct data *head)
{
  struct data *temp, *y;
  printf("\n");
  printf ("enter the position u want to get the data from ");
  int pos, i = 1, j;
  scanf ("%d", &pos);
  temp = head;
   if (pos == 1)
    {
      printf ("%d", temp->a);
    }
  while (i < pos)
    {
      temp = temp->b;
      y = temp;
      i++;
    }

  printf ("%d", y->a);
  printf("\n");

}

void sett (struct data *head)
{
    printf("enter the position and the data to set the element");
    printf("\n");
    int pos,data,i=1;
    scanf("%d %d",&pos,&data);
    struct data *temp,*y;
    temp=head;
    while(i<pos)
    {
        temp=temp->b;
        y=temp;
        i++;
    }
    y->a=data;
    printf("after updating ");
    disp(head);
    printf("\n");
    
    
}

struct data * addp(struct data *head)
{
   int pos,i=1,data;
   struct data *temp,*y,*x;
   x=head;
   struct data *new;
  new = (struct data *) malloc (sizeof (struct data));
  printf("enter the data to add element at a given position");
  printf("\n");
  scanf("%d",&data);
  new->a = data;
   printf("enter the position u want to enter the data");
   printf("\n");
   scanf("%d",&pos);
   temp=x;
   while(i<pos)
   {
       y=temp;
       temp=temp->b;
       i++;
   }
   new->b=y->b;
   y->b=new;
   disp(x);
   return(head);
   
}
struct data * remf(struct data *head)
{
   int pos,i=1; 
   struct data *temp,*y,*x;
   x=head;
   printf("\n");
   printf("enter the position u want to remove the data");
   scanf("%d",&pos);
   
    temp=x;
   while(i<pos)
   {
       y=temp;
       temp=temp->b;
       i++;
   }
   y->b=temp->b;
   temp->b=0;
   disp(x);
   return(head);
}
void suf(struct data*head)
{
 printf("enter the data after which u want to add data after first occurance");
    struct data*temp,*x,*y,*new;
    int data,dat;
    scanf("%d",&data);
    printf("enter the data for the new node");
    scanf("%d",&dat);
    new = (struct data *) malloc (sizeof (struct data));
  new->a = dat;
    temp=head;
    while(temp!=0)

    {
        if((temp->a)==data)
        {
           y=temp; 
           
        }
        if(y!=0)
        {
            break;
        }
        temp=temp->b;
    }
    new->b=y->b;
    y->b=new;
    temp = head;
  printf ("the elements in the linked list are");
  while (temp != 0)
    {
      printf ("%d ", temp->a);
      temp = temp->b;
    }
}
void sud(struct data* head) {
    printf("Enter the data after which you want to delete the node: ");
    struct data* temp = head;
    struct data* x = NULL;
    struct data* y = NULL;
    int data;
    scanf("%d", &data);
    while (temp != NULL) {
        if ((temp->a) == data) {
            y = temp;
            break;
        }
        x = temp;
        temp = temp->b;
    }
    if (y != NULL) {
        if (x == NULL) {
            
            head = y->b;
        } else {
            x->b = y->b;
        }
        free(y); 
    } else {
        printf("Data not found in the linked list.\n");
    }
    temp = head;
    printf("The elements in the linked list are: ");
    while (temp != NULL) {
        printf("%d ", temp->a);
        temp = temp->b;
    }
    printf("\n");
}
void sort(struct data* head1) 
{
    struct data* temp = head1;
    int min, te;

    while (temp != NULL) {
        struct data* current = temp->b;
        min = temp->a;

        while (current != NULL) {
            if (min > current->a) {
                te = min;
                min = current->a;
                current->a = te;
            }
            current = current->b;
        }

        temp->a = min;
        temp = temp->b;
    }
    temp=head1;
    while(temp!=0)
    {
        printf("%d ",temp->a);
        temp=temp->b;
    }
    
}
void reverse(struct data** head1) {
    struct data* prev = NULL;
    struct data* current = *head1;
    struct data* next = NULL;

    while (current != NULL) {
        next = current->b; 
        current->b = prev;  
        prev = current; 
        current = next;
    }
    
*head1 = prev; 
}

void printReversed(struct data* head1) {
    printf("Reversed linked list: ");
    while (head1 != NULL) {
        printf("%d ", head1->a);
        head1 = head1->b;
    }
    printf("\n");
}
void gh(struct data* head1) {
    if (head1 == NULL) {
        return; 
    }
    printf("%d ", head1->a);
    gh(head1->b); 
}
void printReverse(struct data *head)
{
    printf("the reversed linked list is");
    if (head == NULL) {
        return;
    }

    
    printReverse(head->b);

    
} 

int main()
{
    struct data *head = 0;
    struct data *head1 = 0;

    int n, data;
    int end_value;
    int get_pos;
    int set_pos, set_value;
    int add_pos, add_value;
    int remove_pos;
    int add_key, value_after_key;
    int remove_key;
    int sorted_n;
    int insert_sorted_value;

    scanf("%d", &n);

    for (int i = 0; i < n; i++)
    {
        scanf("%d", &data);
        create(data, &head);
    }

    printf("Original list:\n");
    disp(head);
    printf("\n");

    printf("Count:\n");
    count(head);
    printf("\n");

    printf("After removing first:\n");
    removf(head);
    printf("\n");

    scanf("%d", &end_value);
    printf("After adding at end:\n");
    ad(head, end_value);
    printf("\n");

    printf("After removing last:\n");
    re(head);
    printf("\n");

    scanf("%d", &get_pos);
    printf("Element at position:\n");
    po(head);

    scanf("%d %d", &set_pos, &set_value);
    printf("After setting element:\n");
    sett(head);

    scanf("%d %d", &add_pos, &add_value);
    printf("After adding element at position:\n");
    head = addp(head);
    printf("\n");

    scanf("%d", &remove_pos);
    printf("After removing element at position:\n");
    head = remf(head);
    printf("\n");

    scanf("%d %d", &add_key, &value_after_key);
    printf("After adding after first occurrence:\n");
    suf(head);
    printf("\n");

    scanf("%d", &remove_key);
    printf("After removing first occurrence:\n");
    sud(head);
    printf("\n");

    printf("After iterative reverse:\n");
    reverse(&head);
    disp(head);
    printf("\n");

    printf("After sorting:\n");
    sort(head);
    printf("\n");

    printf("Recursive print:\n");
    gh(head);
    printf("\n");

    printf("Recursive reverse print:\n");
    printReverse(head);
    printf("\n");

    printf("After recursive physical reverse:\n");
    printf("Function not implemented\n");

    scanf("%d", &sorted_n);

    for (int i = 0; i < sorted_n; i++)
    {
        scanf("%d", &data);
        createnew(data, &head1);
    }

    printf("Sorted list:\n");
    disp1(head1);
    printf("\n");

    scanf("%d", &insert_sorted_value);

    printf("After sorted insertion:\n");
    printf("Function not implemented\n");

    return 0;
}